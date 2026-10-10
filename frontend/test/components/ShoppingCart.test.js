import { mount } from "@vue/test-utils";
import { defineComponent, nextTick, ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import ShoppingCart from "@/components/product/ShoppingCart.vue";
import { gsap } from "gsap";
import { useProductStore } from "@/stores/product";
import { useLanguageStore } from "@/stores/language";

// Mock gsap
jest.mock("gsap", () => ({
  gsap: {
    fromTo: jest.fn(),
    // Decorative callbacks deliberately never complete.
    timeline: jest.fn(() => ({ fromTo: jest.fn().mockReturnThis() })),
  },
}));

jest.mock("@heroicons/vue/24/outline", () => ({
  XMarkIcon: {
    name: "XMarkIcon",
    template: "<button class='x-mark-icon' @click='$emit(\"click\")'></button>",
  },
}));

const baseStubs = {
  CartProduct: {
    name: "CartProduct",
    props: ["product"],
    template: "<div class='cart-product'>{{ product.title }}</div>",
  },
  RouterLink: {
    name: "RouterLink",
    props: ["to"],
    template: "<a><slot /></a>",
  },
  "router-link": {
    name: "RouterLink",
    props: ["to"],
    template: "<a><slot /></a>",
  },
};

const buildStubs = (overrides = {}) => ({
  ...baseStubs,
  ...overrides,
});

describe("ShoppingCart Component", () => {
  let wrapper;
  let productStore;

  function mountControlledCart() {
    useLanguageStore().setCurrentLanguage("en");
    const CartParent = defineComponent({
      components: { ShoppingCart },
      setup() {
        const visible = ref(true);
        return { visible };
      },
      template: `<div>
        <button data-testid="open-cart" @click="visible = true">Open cart</button>
        <ShoppingCart v-model:visible="visible" />
      </div>`,
    });
    wrapper = mount(CartParent, {
      global: { stubs: buildStubs({ CartProduct: false }) },
    });
  }

  beforeEach(() => {
    setActivePinia(createPinia());
    productStore = useProductStore();
    document.body.style.overflow = "";
    jest.clearAllMocks();
    
    // Setup some products in cart
    productStore.cartProducts = [
      { id: 1, title: "Product 1", price: 100, quantity: 2, gallery_urls: [] },
      { id: 2, title: "Product 2", price: 200, quantity: 1, gallery_urls: [] },
    ];
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
    document.body.style.overflow = "";
    productStore.cartProducts = [];
    localStorage.removeItem("cartProducts");
  });

  test("renders cart when visible", () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: true,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    expect(wrapper.find("h2").text()).toBe("Shopping Cart");
  });

  test("sets body overflow to hidden when visible is true", () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: true,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    expect(document.body.style.overflow).toBe("hidden");
  });

  test("does not render when visible is false and sets body overflow to auto", () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: false,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    // Root div with fixed inset-0 should not be rendered when visible is false
    expect(wrapper.find('[data-testid="cart-overlay"]').exists()).toBe(false);
    expect(document.body.style.overflow).toBe("auto");
  });

  test("displays cart products", () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: true,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    const cartProducts = wrapper.findAll(".cart-product");
    expect(cartProducts.length).toBe(2);
    expect(wrapper.text()).toContain("Product 1");
    expect(wrapper.text()).toContain("Product 2");
  });

  test("clicking the real CartProduct Add link calls store addProductToCart", async () => {
    const addSpy = jest.spyOn(productStore, "addProductToCart");
    productStore.cartProducts = [
      {
        id: 10,
        title: "Product 10",
        price: 150,
        quantity: 1,
        gallery_urls: ["/image-1.jpg"],
      },
    ];
    const firstProduct = productStore.cartProducts[0];

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div />" } },
        { path: "/catalog", name: "catalog", component: { template: "<div />" } },
        { path: "/checkout", name: "checkout", component: { template: "<div />" } },
      ],
    });

    router.push("/");
    await router.isReady();

    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: { plugins: [router], stubs: { XMarkIcon: true } },
    });

    const cartProduct = wrapper.findComponent({ name: "CartProduct" });
    expect(cartProduct.exists()).toBe(true);

    const addLink = cartProduct.findAll("a").find((link) => link.text() === "Add");
    await addLink.trigger("click");

    expect(addSpy).toHaveBeenCalledWith(firstProduct);
  });

  test("clicking the real CartProduct Remove link calls store removeProductFromCart", async () => {
    const removeSpy = jest.spyOn(productStore, "removeProductFromCart");
    productStore.cartProducts = [
      {
        id: 10,
        title: "Product 10",
        price: 150,
        quantity: 1,
        gallery_urls: ["/image-1.jpg"],
      },
    ];
    const firstProduct = productStore.cartProducts[0];

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div />" } },
        { path: "/catalog", name: "catalog", component: { template: "<div />" } },
        { path: "/checkout", name: "checkout", component: { template: "<div />" } },
      ],
    });

    router.push("/");
    await router.isReady();

    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: { plugins: [router], stubs: { XMarkIcon: true } },
    });

    const cartProduct = wrapper.findComponent({ name: "CartProduct" });
    expect(cartProduct.exists()).toBe(true);

    const removeLink = cartProduct.findAll("a").find((link) => link.text() === "Remove");
    await removeLink.trigger("click");

    expect(removeSpy).toHaveBeenCalledWith(firstProduct);
  });

  test("renders RouterLinks inside shopping cart with memory router", async () => {
    productStore.cartProducts = [
      {
        id: 10,
        title: "Product 10",
        price: 150,
        quantity: 1,
        gallery_urls: ["/image-1.jpg"],
      },
    ];

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div />" } },
        { path: "/catalog", name: "catalog", component: { template: "<div />" } },
        { path: "/checkout", name: "checkout", component: { template: "<div />" } },
      ],
    });

    router.push("/");
    await router.isReady();

    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: { plugins: [router], stubs: { XMarkIcon: true } },
    });

    const routerLinks = wrapper.findAllComponents({ name: "RouterLink" });
    expect(routerLinks.length).toBeGreaterThan(0);
  });

  test("displays total price", () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: true,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    // Total should be 100*2 + 200*1 = 400
    expect(wrapper.text()).toContain("400");
  });

  test("displays empty cart message when no products", () => {
    productStore.cartProducts = [];

    wrapper = mount(ShoppingCart, {
      props: {
        visible: true,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    expect(wrapper.text()).toContain("No products");
    expect(wrapper.text()).toContain("Continue Shopping");
  });

  test.each(['cart-overlay', 'cart-close'])('closes through %s without animation completion', async (testId) => {
    mountControlledCart();

    await wrapper.get(`[data-testid="${testId}"]`).trigger("click");

    expect(wrapper.find('[data-testid="cart-overlay"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="cart-close"]').exists()).toBe(false);
    expect(document.body.style.overflow).toBe("auto");
  });

  test("renders checkout button when products exist", () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: true,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    expect(wrapper.text()).toContain("Checkout");
    expect(wrapper.text()).toContain("Subtotal");
  });

  test("renders total price from store in the cart footer", () => {
    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: { stubs: buildStubs() },
    });

    const expectedTotal = productStore.totalCartPrice;
    expect(wrapper.text()).toContain(String(expectedTotal));
    expect(productStore.cartProducts.length).toBe(2);
  });

  test("renders correctly regardless of current language setting", () => {
    const languageStore = useLanguageStore();
    languageStore.setCurrentLanguage("es");

    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: { stubs: buildStubs() },
    });

    expect(languageStore.getCurrentLanguage).toBe("es");
    expect(wrapper.find("h2").text()).toBe("Shopping Cart");
  });

  test("reopens the preserved cart without animation completion", async () => {
    localStorage.setItem("cartProducts", JSON.stringify(productStore.cartProducts));
    mountControlledCart();
    await nextTick();
    const storedCart = localStorage.getItem("cartProducts");

    await wrapper.get('[data-testid="cart-close"]').trigger("click");
    expect(wrapper.find('[data-testid="cart-overlay"]').exists()).toBe(false);
    await wrapper.get('[data-testid="open-cart"]').trigger("click");

    expect(wrapper.find('[data-testid="cart-overlay"]').exists()).toBe(true);
    expect({
      titles: wrapper.findAllComponents({ name: "CartProduct" }).map((item) => item.get("h3").text()),
      lines: wrapper.findAllComponents({ name: "CartProduct" }).map((item) =>
        item.findAll("p").map((paragraph) => paragraph.text())
      ),
      subtotal: wrapper.find("span").text(),
    }).toEqual({
      titles: ["Product 1", "Product 2"],
      lines: [["$200", "Qty 2"], ["$200", "Qty 1"]],
      subtotal: "$ 400",
    });
    expect(localStorage.getItem("cartProducts")).toBe(storedCart);
    expect(document.body.style.overflow).toBe("hidden");

    await wrapper.get('[data-testid="cart-overlay"]').trigger("click");
    expect(wrapper.find('[data-testid="cart-overlay"]').exists()).toBe(false);
    expect(document.body.style.overflow).toBe("auto");
  });

  test("runs open animations after toggling visibility to true", async () => {
    wrapper = mount(ShoppingCart, {
      props: {
        visible: false,
      },
      global: {
        stubs: buildStubs(),
      },
    });

    await wrapper.setProps({ visible: true });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(document.body.style.overflow).toBe("hidden");
    expect(gsap.fromTo.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  test("CartProduct removeProduct event with id looks up and removes correct item", async () => {
    const removeSpy = jest.spyOn(productStore, "removeProductFromCart");
    const firstProduct = productStore.cartProducts[0];

    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: {
        stubs: buildStubs({
          CartProduct: {
            props: ["product"],
            template: "<div><button class='remove-id' @click=\"$emit('removeProduct', product.id)\"></button></div>",
          },
        }),
      },
    });

    await wrapper.find(".remove-id").trigger("click");

    expect(removeSpy).toHaveBeenCalledWith(firstProduct);
  });

  test("handleRemoveProduct with numeric id not in cart does not call removeProductFromCart", async () => {
    const removeSpy = jest.spyOn(productStore, "removeProductFromCart");

    wrapper = mount(ShoppingCart, {
      props: { visible: true },
      global: {
        stubs: buildStubs({
          CartProduct: {
            props: ["product"],
            template: "<div><button class='remove-unknown' @click=\"$emit('removeProduct', 9999)\"></button></div>",
          },
        }),
      },
    });

    await wrapper.find(".remove-unknown").trigger("click");

    expect(removeSpy).not.toHaveBeenCalled();
  });
});
