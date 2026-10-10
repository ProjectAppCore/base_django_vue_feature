import { ref, computed } from "vue";
import { defineStore } from "pinia";
import { create_request, get_request } from "./services/request_http";

const normalizeMediaUrl = (url) => {
  if (!url || typeof url !== 'string') return url;
  const mediaIndex = url.indexOf('/media/');
  if (mediaIndex === -1) return url;
  return url.slice(mediaIndex);
};

export const useProductStore = defineStore("productStore", () => {
  const products = ref([]);
  const categories = ref([]);
  const filteredProducts = ref([]);
  const cartProducts = ref([]);
  const dataLoaded = ref(false);

  /**
   * Get product by ID.
   * @param {number} productId - Product ID.
   * @returns {object|undefined} - Product object or undefined.
   */
  const productById = computed(() => (productId) =>
    products.value.find((product) => product.id === productId)
  );

  /**
   * Filter products by name.
   * @param {string} name - Search term.
   * @returns {Array} - Matching products.
   */
  const productsByName = computed(() => (name) => {
    const lowerCaseName = name.toLowerCase();
    return products.value.filter((product) =>
      product.title.toLowerCase().includes(lowerCaseName)
    );
  });

  /**
   * Calculate total number of products in the cart.
   * @returns {number} - Total quantity.
   */
  const totalCartProducts = computed(() =>
    cartProducts.value.reduce((total, product) => total + product.quantity, 0)
  );

  /**
   * Calculate total price of products in the cart.
   * @returns {number} - Total price.
   */
  const totalCartPrice = computed(() =>
    cartProducts.value.reduce(
      (total, product) => total + parseFloat(product.price) * product.quantity,
      0
    )
  );

  /**
   * Fetches the list of products from the backend.
   */
  async function fetchProducts() {
    if (dataLoaded.value) return;

    try {
      const response = await get_request("products/");
      products.value = Array.isArray(response.data)
        ? response.data.map((p) => ({
            ...p,
            gallery_urls: Array.isArray(p.gallery_urls)
              ? p.gallery_urls.map(normalizeMediaUrl)
              : [],
          }))
        : [];
      dataLoaded.value = true;
      filteredProducts.value = products.value;
      fetchUniqueCategoriesAndSubCategories();
    } catch (error) {
      console.error("Failed to fetch products:", error);
    }
  }

  /**
   * Add product to the cart.
   * @param {Object} addProduct - The product to add.
   * @param {number} quantity - Quantity to add.
   */
  function addProductToCart(addProduct, quantity) {
    const existingProduct = cartProducts.value.find(
      (product) => product.id === addProduct.id
    );

    if (existingProduct) {
      existingProduct.quantity += quantity ? quantity : 1;
    } else {
      cartProducts.value.push({ ...addProduct, quantity: quantity ? quantity : 1 });
    }
    localStorage.setItem("cartProducts", JSON.stringify(cartProducts.value));
  }

  /**
   * Remove product from the cart.
   * @param {Object} removeProduct - The product to remove.
   */
  function removeProductFromCart(removeProduct) {
    const removeProductFound = cartProducts.value.find(
      (product) => product === removeProduct
    );

    if (removeProductFound.quantity > 1) {
      removeProductFound.quantity -= 1;
    } else {
      cartProducts.value = cartProducts.value.filter(
        (product) => product !== removeProductFound
      );
    }
    localStorage.setItem("cartProducts", JSON.stringify(cartProducts.value));
  }

  /**
   * Filter products by sub-category.
   */
  function productBySubCategory() {
    const isChecked = (subCategory) => subCategory.checked;

    filteredProducts.value = products.value.filter((product) =>
      categories.value.some((category) =>
        category.subCategories.some(
          (subCategory) =>
            isChecked(subCategory) && product.sub_category === subCategory.name
        )
      )
    );

    if (filteredProducts.value.length === 0)
      filteredProducts.value = products.value;
  }

  /**
   * Fetch unique categories and subCategories from products.
   */
  async function fetchUniqueCategoriesAndSubCategories() {
    if (!dataLoaded.value) await fetchProducts();

    const categoryMap = new Map();

    products.value.forEach((product) => {
      if (!categoryMap.has(product.category)) {
        categoryMap.set(product.category, {
          name: product.category,
          subCategories: [],
        });
      }
      categoryMap
        .get(product.category)
        .subCategories.push({ name: product.sub_category, checked: false });
    });

    categories.value = Array.from(categoryMap.values()).map((category) => ({
      ...category,
      subCategories: Array.from(
        new Set(category.subCategories.map((sub) => JSON.stringify(sub)))
      ).map((sub) => JSON.parse(sub)),
    }));
  }

  /**
   * Create a new sale.
   * @param {Object} form - The form data for the sale.
   * @returns {number} - The response status.
   * @throws {Error} - When the request fails.
   */
  async function createSale(form) {
    const response = await create_request("create-sale/", {
      email: form.email,
      address: form.address,
      city: form.city,
      state: form.state,
      postal_code: form.postalCode,
      sold_products: form.soldProducts,
    });
    return response.status;
  }

  return {
    products,
    categories,
    filteredProducts,
    cartProducts,
    dataLoaded,
    productById,
    productsByName,
    totalCartProducts,
    totalCartPrice,
    fetchProducts,
    addProductToCart,
    removeProductFromCart,
    productBySubCategory,
    fetchUniqueCategoriesAndSubCategories,
    createSale,
  };
});
