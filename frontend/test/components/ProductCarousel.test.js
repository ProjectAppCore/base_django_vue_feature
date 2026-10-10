import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';

jest.mock('@/services/http/client', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

jest.mock('@/services/http/tokens', () => ({
  getAccessToken: jest.fn(() => null),
  getRefreshToken: jest.fn(() => null),
  setTokens: jest.fn(),
  clearTokens: jest.fn(),
}));

import httpClient from '@/services/http/client';
import { useLanguageStore } from '@/stores/language';
import ProductCarousel from '@/components/product/ProductCarousel.vue';

const sampleProducts = Array.from({ length: 6 }, (_, i) => ({
  id: i + 1,
  title: `Product ${i + 1}`,
  price: (i + 1) * 10,
  gallery_urls: [`/img/product-${i + 1}.jpg`],
}));

function buildRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div />' } },
      { path: '/catalog', name: 'catalog', component: { template: '<div />' } },
      { path: '/product/:product_id', name: 'product', component: { template: '<div />' } },
    ],
  });
}

describe('ProductCarousel responsive grid', () => {
  let router;

  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
    router = buildRouter();
    httpClient.get.mockResolvedValue({ data: sampleProducts });
  });

  async function renderGrid() {
    await router.push('/');
    await router.isReady();
    const wrapper = mount(ProductCarousel, { global: { plugins: [router] } });
    await flushPromises();
    return wrapper;
  }

  test('shows received products in their original order', async () => {
    const wrapper = await renderGrid();

    const titles = wrapper.findAll('[data-testid="product-carousel-item"] h3').map((item) => item.text());
    expect(titles).toEqual(sampleProducts.map((item) => item.title));
  });

  test('shows the received price for each product', async () => {
    const wrapper = await renderGrid();

    const values = wrapper.findAll('[data-testid="product-carousel-item"] p').map((item) => item.text());
    expect(values).toEqual(sampleProducts.map((item) => `$${item.price}`));
  });

  test('shows the received image for each product', async () => {
    const wrapper = await renderGrid();

    const images = wrapper.findAll('[data-testid="product-carousel-item"] img').map((item) => item.attributes('src'));
    expect(images).toEqual(sampleProducts.map((item) => item.gallery_urls[0]));
  });

  test('renders no grid when the response is empty', async () => {
    httpClient.get.mockResolvedValue({ data: [] });
    const wrapper = await renderGrid();

    expect(wrapper.find('[data-testid="product-carousel-list"]').exists()).toBe(false);
  });

  test('opens the last product through its card', async () => {
    const wrapper = await renderGrid();

    await wrapper.findAll('[data-testid="product-carousel-item"]').at(-1).trigger('click');
    await flushPromises();

    expect(router.currentRoute.value.path).toBe('/product/6');
  });

  test('opens the catalog through its existing link', async () => {
    const wrapper = await renderGrid();
    const link = wrapper.findAll('a').find((item) => item.text() === 'SHOP NOW');

    await link.trigger('click');
    await flushPromises();

    expect(router.currentRoute.value.path).toBe('/catalog');
  });

  test('preserves the non-English title behavior', async () => {
    useLanguageStore().setCurrentLanguage('es');
    const wrapper = await renderGrid();

    expect(wrapper.findAll('[data-testid="product-carousel-item"] h3 span')).toHaveLength(0);
    expect(wrapper.get('[data-testid="product-carousel-item"] p').text()).toBe('$10');
  });
});
