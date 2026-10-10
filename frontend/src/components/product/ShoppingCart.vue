<template>
    <!-- Shopping Cart Overlay -->
    <div class="fixed inset-0 flex justify-end z-50" v-if="visible">
        <div
            @click="closeCart()"
            class="absolute inset-0 bg-foreground/40 backdrop-blur-md" data-testid="cart-overlay">
        </div>
        <div class="relative bg-card text-card-foreground h-full w-full lg:w-2/5 shadow-lg flex flex-col z-60">
            <!-- Cart Header -->
            <div class="flex justify-between items-center p-10">
                <h2 class="text-2xl font-semibold">Shopping Cart</h2>
                <button @click="closeCart()" data-testid="cart-close" class="cursor-pointer">
                    <XMarkIcon class="text-muted-foreground w-6 h-6" />
                </button>
            </div>

            <!-- Cart Items -->
            <div v-if="cartProducts.length" class="p-10 space-y-4 flex-1 overflow-y-auto">
                <CartProduct v-for="product in cartProducts" 
                    :key="product.id" 
                    :product="product"
                    @addProduct="handleAddProduct" 
                    @removeProduct="handleRemoveProduct" />
            </div>
            <div v-else class="text-lg ps-10">
                <p>No products</p>
                <RouterLink :to="{ name: 'catalog' }" class="cursor-pointer border-b border-foreground">
                    Continue Shopping
                </RouterLink>
            </div>

            <!-- Cart Footer -->
            <div v-if="cartProducts.length" class="border-t border-border p-4">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="text-2xl font-semibold">Subtotal</h3>
                        <p class="text-md text-muted-foreground font-medium">
                            Shipping calculated at checkout.
                        </p>
                    </div>
                    <span class="text-xl font-semibold">$ {{ cartTotalPrice }}</span>
                </div>
                <router-link :to="{ name: 'checkout' }">
                    <button
                        class="w-full mt-4 bg-primary text-primary-foreground py-2 rounded-lg hover:bg-primary/90 font-medium text-xl tracking-wide">
                        Checkout
                    </button>
                </router-link>
                <div class="text-center mt-4 text-lg">
                    <RouterLink :to="{ name: 'catalog' }" class="cursor-pointer border-b-2 border-foreground">
                        Or Continue Shopping
                    </RouterLink>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { computed, watchEffect } from "vue";
    import CartProduct from "./CartProduct.vue";
    import { XMarkIcon } from "@heroicons/vue/24/outline";
    import { useLanguageStore } from "@/stores/language.js";
    import { useProductStore } from "@/stores/product";

    const appStore = useLanguageStore();
    /* istanbul ignore next */
    const currentLanguage = computed(() => appStore.getCurrentLanguage);

    // Product store references
    const productStore = useProductStore();
    const cartProducts = computed(() => productStore.cartProducts);
    const cartTotalPrice = computed(() => productStore.totalCartPrice);

    // Props definition
    const props = defineProps({
        visible: {
            type: Boolean,
            required: true,
        },
    });
    const emit = defineEmits(["update:visible"]);

    // Lock page scrolling while the cart is visible.
    watchEffect(() => {
        document.body.style.overflow = props.visible ? "hidden" : "auto";
    });

    const closeCart = () => {
        emit("update:visible", false);
    };

    /**
     * Add product to cart
     * @param {Object} product - The product to add
     */
    const addProduct = (product) => {
        productStore.addProductToCart(product);
    };

    /**
     * Remove product from cart
     * @param {Number} productId - The ID of the product to remove
     */
    const removeProduct = (product) => {
        productStore.removeProductFromCart(product);
    };

    const handleAddProduct = (product) => {
        addProduct(product);
    };

    const handleRemoveProduct = (payload) => {
        const product = typeof payload === "object"
            ? payload
            : productStore.cartProducts.find((item) => item.id === payload);

        if (product) {
            removeProduct(product);
        }
    };
    /* istanbul ignore next */
</script>
