import { setActivePinia, createPinia } from "pinia";
import { useProductStore } from "@/stores/product";

// Mock the request_http module
jest.mock("@/stores/services/request_http", () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
}));

import { get_request, create_request } from "@/stores/services/request_http";

describe("Product Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe("Initial State", () => {
    test("should initialize with default state", () => {
      const store = useProductStore();
      expect(store.products).toEqual([]);
      expect(store.categories).toEqual([]);
      expect(store.filteredProducts).toEqual([]);
      expect(store.cartProducts).toEqual([]);
      expect(store.dataLoaded).toBe(false);
    });
  });

  describe("Getters", () => {
    test("productById should return product by id", () => {
      const store = useProductStore();
      store.products = [
        { id: 1, title: "Product 1", price: 100 },
        { id: 2, title: "Product 2", price: 200 },
      ];

      const product = store.productById(1);
      expect(product).toEqual({ id: 1, title: "Product 1", price: 100 });
    });

    test("productsByName should filter products by name", () => {
      const store = useProductStore();
      store.products = [
        { id: 1, title: "Beautiful Candle", price: 100 },
        { id: 2, title: "Greek Sculpture", price: 200 },
        { id: 3, title: "Modern Candle", price: 150 },
      ];

      const results = store.productsByName("candle");
      expect(results).toHaveLength(2);
      expect(results[0].title).toContain("Candle");
    });

    test("totalCartProducts should calculate total quantity", () => {
      const store = useProductStore();
      store.cartProducts = [
        { id: 1, title: "Product 1", price: 100, quantity: 2 },
        { id: 2, title: "Product 2", price: 200, quantity: 3 },
      ];

      expect(store.totalCartProducts).toBe(5);
    });

    test("totalCartPrice should calculate total price", () => {
      const store = useProductStore();
      store.cartProducts = [
        { id: 1, title: "Product 1", price: 100, quantity: 2 },
        { id: 2, title: "Product 2", price: 200, quantity: 3 },
      ];

      expect(store.totalCartPrice).toBe(800); // 100*2 + 200*3
    });
  });

  describe("Actions - fetchProducts", () => {
    test("should fetch products successfully", async () => {
      const store = useProductStore();
      const mockProducts = [
        { id: 1, title: "Product 1", category: "Cat1", sub_category: "Sub1", gallery_urls: [] },
        { id: 2, title: "Product 2", category: "Cat2", sub_category: "Sub2", gallery_urls: [] },
      ];

      get_request.mockResolvedValue({ data: mockProducts });

      await store.fetchProducts();

      expect(store.products).toEqual(mockProducts);
      expect(store.dataLoaded).toBe(true);
      expect(store.filteredProducts).toEqual(mockProducts);
    });

    test("should not fetch if data already loaded", async () => {
      const store = useProductStore();
      store.dataLoaded = true;

      await store.fetchProducts();

      expect(get_request).not.toHaveBeenCalled();
    });

    test("should handle fetch error", async () => {
      const store = useProductStore();
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});

      get_request.mockRejectedValue(new Error("Network error"));

      await store.fetchProducts();

      expect(store.products).toEqual([]);
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });

    test("should handle non-array response data", async () => {
      const store = useProductStore();
      get_request.mockResolvedValue({ data: { message: "not-array" } });

      await store.fetchProducts();

      expect(store.products).toEqual([]);
      expect(store.filteredProducts).toEqual([]);
      expect(store.dataLoaded).toBe(true);
    });

    test("should normalize gallery_urls media paths", async () => {
      const store = useProductStore();
      const mockProducts = [
        {
          id: 1,
          title: "Product 1",
          category: "Cat1",
          sub_category: "Sub1",
          gallery_urls: [
            "/media/img1.jpg",
            "http://localhost:8000/media/img2.jpg",
            null,
            "https://example.com/other.png",
          ],
        },
        {
          id: 2,
          title: "Product 2",
          category: "Cat2",
          sub_category: "Sub2",
          gallery_urls: null,
        },
      ];

      get_request.mockResolvedValue({ data: mockProducts });

      await store.fetchProducts();

      expect(store.products[0].gallery_urls).toEqual([
        "/media/img1.jpg",
        "/media/img2.jpg",
        null,
        "https://example.com/other.png",
      ]);
      expect(store.products[1].gallery_urls).toEqual([]);
    });
  });

  describe("Actions - Cart Management", () => {
    test("addProductToCart should add new product", () => {
      const store = useProductStore();
      const product = { id: 1, title: "Product 1", price: 100 };

      store.addProductToCart(product);

      expect(store.cartProducts).toHaveLength(1);
      expect(store.cartProducts[0].quantity).toBe(1);
    });

    test("addProductToCart should increment quantity if product exists", () => {
      const store = useProductStore();
      const product = { id: 1, title: "Product 1", price: 100 };

      store.addProductToCart(product);
      store.addProductToCart(product);

      expect(store.cartProducts).toHaveLength(1);
      expect(store.cartProducts[0].quantity).toBe(2);
    });

    test("addProductToCart should increment by custom quantity when product exists", () => {
      const store = useProductStore();
      const product = { id: 1, title: "Product 1", price: 100 };

      store.addProductToCart(product, 2);
      store.addProductToCart(product, 3);

      expect(store.cartProducts).toHaveLength(1);
      expect(store.cartProducts[0].quantity).toBe(5);
    });

    test("addProductToCart should add with custom quantity", () => {
      const store = useProductStore();
      const product = { id: 1, title: "Product 1", price: 100 };

      store.addProductToCart(product, 5);

      expect(store.cartProducts[0].quantity).toBe(5);
    });

    test("removeProductFromCart should decrement quantity", () => {
      const store = useProductStore();
      const product = { id: 1, title: "Product 1", price: 100 };

      store.addProductToCart(product, 3);
      store.removeProductFromCart(store.cartProducts[0]);

      expect(store.cartProducts[0].quantity).toBe(2);
    });

    test("removeProductFromCart should remove product when quantity is 1", () => {
      const store = useProductStore();
      const product = { id: 1, title: "Product 1", price: 100 };

      store.addProductToCart(product);
      store.removeProductFromCart(store.cartProducts[0]);

      expect(store.cartProducts).toHaveLength(0);
    });
  });

  describe("Actions - Category Management", () => {
    test("fetchUniqueCategoriesAndSubCategories should extract unique categories", async () => {
      const store = useProductStore();
      const mockProducts = [
        { id: 1, category: "Candles", sub_category: "Greek" },
        { id: 2, category: "Candles", sub_category: "Modern" },
        { id: 3, category: "Decor", sub_category: "Trending" },
      ];

      get_request.mockResolvedValue({ data: mockProducts });

      await store.fetchProducts();

      expect(store.categories).toHaveLength(2);
      expect(store.categories[0].name).toBe("Candles");
      expect(store.categories[0].subCategories).toHaveLength(2);
    });

    test("fetchUniqueCategoriesAndSubCategories fetches when data not loaded", async () => {
      const store = useProductStore();
      const mockProducts = [
        { id: 1, category: "Candles", sub_category: "Greek" },
      ];

      store.dataLoaded = false;
      get_request.mockResolvedValue({ data: mockProducts });

      await store.fetchUniqueCategoriesAndSubCategories();

      expect(get_request).toHaveBeenCalled();
      expect(store.categories).toHaveLength(1);
    });

    test("productBySubCategory should filter products", () => {
      const store = useProductStore();
      store.products = [
        { id: 1, category: "Candles", sub_category: "Greek" },
        { id: 2, category: "Candles", sub_category: "Modern" },
      ];
      store.categories = [
        {
          name: "Candles",
          subCategories: [
            { name: "Greek", checked: true },
            { name: "Modern", checked: false },
          ],
        },
      ];

      store.productBySubCategory();

      expect(store.filteredProducts).toHaveLength(1);
      expect(store.filteredProducts[0].sub_category).toBe("Greek");
    });

    test("productBySubCategory should show all if no filters", () => {
      const store = useProductStore();
      store.products = [
        { id: 1, category: "Candles", sub_category: "Greek" },
        { id: 2, category: "Candles", sub_category: "Modern" },
      ];
      store.categories = [
        {
          name: "Candles",
          subCategories: [
            { name: "Greek", checked: false },
            { name: "Modern", checked: false },
          ],
        },
      ];

      store.productBySubCategory();

      expect(store.filteredProducts).toEqual(store.products);
    });
  });

  describe("Actions - createSale", () => {
    test("should create sale successfully", async () => {
      const store = useProductStore();
      const form = {
        email: "test@example.com",
        address: "123 Main St",
        city: "City",
        state: "State",
        postalCode: "12345",
        soldProducts: [{ product_id: 1, quantity: 2 }],
      };

      create_request.mockResolvedValue({ status: 201 });

      const status = await store.createSale(form);

      expect(status).toBe(201);
      expect(create_request).toHaveBeenCalledWith("create-sale/", {
        email: form.email,
        address: form.address,
        city: form.city,
        state: form.state,
        postal_code: form.postalCode,
        sold_products: form.soldProducts,
      });
    });

    test("should propagate createSale rejection", async () => {
      const store = useProductStore();
      const form = {
        email: "test@example.com",
        address: "123 Main St",
        city: "City",
        state: "State",
        postalCode: "12345",
        soldProducts: [],
      };

      const error = new Error("Server error");
      create_request.mockRejectedValue(error);

      await expect(store.createSale(form)).rejects.toBe(error);
    });
  });
});
