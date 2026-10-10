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
import BlogCarousel from '@/components/blog/BlogCarousel.vue';

const sampleBlogs = Array.from({ length: 6 }, (_, i) => ({
  id: i + 1,
  title: `Blog ${i + 1}`,
  category: `Category ${i + 1}`,
  image_url: `/img/blog-${i + 1}.jpg`,
}));

function buildRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div />' } },
      { path: '/blogs', name: 'blogs', component: { template: '<div />' } },
      { path: '/blog/:blog_id', name: 'blog', component: { template: '<div />' } },
    ],
  });
}

describe('BlogCarousel responsive grid', () => {
  let router;

  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
    router = buildRouter();
    httpClient.get.mockResolvedValue({ data: sampleBlogs });
  });

  async function renderGrid() {
    await router.push('/');
    await router.isReady();
    const wrapper = mount(BlogCarousel, { global: { plugins: [router] } });
    await flushPromises();
    return wrapper;
  }

  test('shows received blogs in their original order', async () => {
    const wrapper = await renderGrid();

    const titles = wrapper.findAll('[data-testid="blog-carousel-item"] h3').map((item) => item.text());
    expect(titles).toEqual(sampleBlogs.map((item) => item.title));
  });

  test('shows the received category for each blog', async () => {
    const wrapper = await renderGrid();

    const values = wrapper.findAll('[data-testid="blog-carousel-item"] p').map((item) => item.text());
    expect(values).toEqual(sampleBlogs.map((item) => item.category));
  });

  test('shows the received image for each blog', async () => {
    const wrapper = await renderGrid();

    const images = wrapper.findAll('[data-testid="blog-carousel-item"] img').map((item) => item.attributes('src'));
    expect(images).toEqual(sampleBlogs.map((item) => item.image_url));
  });

  test('renders no grid when the response is empty', async () => {
    httpClient.get.mockResolvedValue({ data: [] });
    const wrapper = await renderGrid();

    expect(wrapper.find('[data-testid="blog-carousel-list"]').exists()).toBe(false);
  });

  test('opens the last blog through its card', async () => {
    const wrapper = await renderGrid();

    await wrapper.findAll('[data-testid="blog-carousel-item"]').at(-1).trigger('click');
    await flushPromises();

    expect(router.currentRoute.value.path).toBe('/blog/6');
  });

  test('opens the blogs through its existing link', async () => {
    const wrapper = await renderGrid();
    const link = wrapper.findAll('a').find((item) => item.text() === 'Explore now');

    await link.trigger('click');
    await flushPromises();

    expect(router.currentRoute.value.path).toBe('/blogs');
  });

  test('preserves the non-English title behavior', async () => {
    useLanguageStore().setCurrentLanguage('es');
    const wrapper = await renderGrid();

    expect(wrapper.findAll('[data-testid="blog-carousel-item"] h3 span')).toHaveLength(0);
    expect(wrapper.get('[data-testid="blog-carousel-item"] p').text()).toBe('Category 1');
  });
});
