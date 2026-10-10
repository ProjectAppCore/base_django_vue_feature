import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import Checkout from '@/views/product/Checkout.vue';
import { useProductStore } from '@/stores/product';
import { useLanguageStore } from '@/stores/language';
import api from '@/services/http/client';
import Swal from 'sweetalert2';

jest.mock('@/services/http/client', () => ({ post: jest.fn() }));
jest.mock('sweetalert2', () => ({ fire: jest.fn() }));

async function mountCheckout() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div />' } },
      { path: '/checkout', name: 'checkout', component: Checkout },
    ],
  });
  await router.push('/checkout');
  const store = useProductStore();
  store.addProductToCart({
    id: 7, title: 'Test candle', price: 100, gallery_urls: ['/media/candle.jpg'],
  }, 2);
  const wrapper = mount(Checkout, { global: { plugins: [router] } });
  for (const [field, value] of Object.entries({
    email: 'buyer@example.com', 'card-number': '4111111111111111',
    expiry: '12/28', cvc: '123', address: '123 Main St',
    city: 'City', state: 'State', 'postal-code': '12345',
  })) {
    await wrapper.get(`[data-testid="checkout-${field}"]`).setValue(value);
  }
  return { wrapper, store, router };
}

describe('Checkout order confirmation', () => {
  let consoleError;

  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    jest.clearAllMocks();
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => consoleError.mockRestore());

  test('keeps the order pending until creation is confirmed', async () => {
    let resolveRequest;
    api.post.mockImplementation(() => new Promise((resolve) => { resolveRequest = resolve; }));
    const { wrapper, store, router } = await mountCheckout();

    await wrapper.get('form').trigger('submit');

    expect(wrapper.get('button[type="submit"]').element.disabled).toBe(true);
    expect(store.cartProducts).toHaveLength(1);
    expect(JSON.parse(localStorage.getItem('cartProducts'))).toEqual(store.cartProducts);
    expect(router.currentRoute.value.path).toBe('/checkout');
    expect(Swal.fire.mock.calls).toEqual([]);
    resolveRequest({ status: 201 });
    await flushPromises();
    wrapper.unmount();
  });

  test('ignores another submit while creation is pending', async () => {
    let resolveRequest;
    api.post.mockImplementation(() => new Promise((resolve) => { resolveRequest = resolve; }));
    const { wrapper } = await mountCheckout();

    await wrapper.get('form').trigger('submit');
    await wrapper.get('form').trigger('submit');

    expect(api.post).toHaveBeenCalledTimes(1);
    resolveRequest({ status: 201 });
    await flushPromises();
    wrapper.unmount();
  });

  test('completes checkout after the backend creates the order', async () => {
    api.post.mockResolvedValue({ status: 201 });
    const { wrapper, store, router } = await mountCheckout();

    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(api.post).toHaveBeenCalledWith('create-sale/', {
      email: 'buyer@example.com', address: '123 Main St', city: 'City',
      state: 'State', postal_code: '12345',
      sold_products: [{ product_id: 7, quantity: 2 }],
    });
    expect(store.cartProducts).toEqual([]);
    expect(localStorage.getItem('cartProducts')).toBeNull();
    expect(Swal.fire).toHaveBeenCalledWith({ title: 'Order created successfully', icon: 'success' });
    expect(router.currentRoute.value.path).toBe('/');
    wrapper.unmount();
  });

  test.each([
    ['HTTP 400', { response: { status: 400 } }],
    ['HTTP 500', { response: { status: 500 } }],
    ['network rejection', new Error('Network unavailable')],
  ])('preserves checkout after %s', async (_name, error) => {
    api.post.mockRejectedValue(error);
    const { wrapper, store, router } = await mountCheckout();

    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toContain('Your cart has been kept');
    expect(store.cartProducts).toHaveLength(1);
    expect(JSON.parse(localStorage.getItem('cartProducts'))).toEqual(store.cartProducts);
    expect(wrapper.get('[data-testid="checkout-email"]').element.value).toBe('buyer@example.com');
    expect(router.currentRoute.value.path).toBe('/checkout');
    expect(wrapper.get('button[type="submit"]').element.disabled).toBe(false);
    wrapper.unmount();
  });

  test('shows the failure in the current language', async () => {
    api.post.mockRejectedValue(new Error('Network unavailable'));
    useLanguageStore().setCurrentLanguage('es');
    const { wrapper } = await mountCheckout();

    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toBe(
      'No pudimos crear tu pedido. Conservamos tu carrito. Inténtalo de nuevo.',
    );
    wrapper.unmount();
  });

  test('requires the creation status before clearing the cart', async () => {
    api.post.mockResolvedValue({ status: 200 });
    const { wrapper, store } = await mountCheckout();

    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toContain('We could not create your order');
    expect(store.cartProducts).toHaveLength(1);
    wrapper.unmount();
  });
});
