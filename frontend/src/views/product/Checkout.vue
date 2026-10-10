<template>
    <div class="flex flex-col">
        <!-- Header -->
        <header class="flex justify-between items-center px-8 py-2">
            <router-link :to="{ name: 'home' }">
                <img src="" alt="Logo" class="h-20 cursor-pointer" />
            </router-link>

            <div class="hidden lg:flex items-center space-x-4">
                <LockClosedIcon class="w-6 h-6"></LockClosedIcon>
                <div class="flex items-center space-x-2">
                    <span class="text-lg font-bold">
                        Purchase Safety
                    </span>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="w-full grid lg:grid-cols-2 min-h-screen">
            <!-- Left Column -->
            <div class="relative w-full order-2 lg:order-1">
                <form @submit.prevent="handleSubmit" class="sticky top-0 py-8 px-8">
                    <h2 class="text-3xl font-semibold">
                        Contact Information
                    </h2>
                    <div class="mt-4">
                        <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                            Email Address
                        </label>
                        <input type="email" v-model="form.email"
                            class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                            data-testid="checkout-email"
                            required />
                    </div>

                    <h2 class="text-3xl font-semibold mt-6">
                        Payment details
                    </h2>
                    <div class="mt-4">
                        <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                            Card Number
                        </label>
                        <input type="text" v-model="form.cardNumber"
                            class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                            data-testid="checkout-card-number"
                            required />
                    </div>
                    <div class="mt-4 grid grid-cols-4 gap-4">
                        <div class="col-span-3">
                            <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                                Expiration Date
                            </label>
                            <input type="text" v-model="form.expirationDate"
                                class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                                data-testid="checkout-expiry"
                                required />
                        </div>
                        <div class="col-span-1">
                            <label class="block text-muted-foreground mb-2 font-semibold text-lg">CVC</label>
                            <input type="text" v-model="form.cvc"
                                class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                                data-testid="checkout-cvc"
                                required />
                        </div>
                    </div>

                    <h2 class="text-3xl font-semibold mt-6">
                        Shipping Address
                    </h2>
                    <div class="mt-4">
                        <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                            Address
                        </label>
                        <input type="text" v-model="form.address"
                            class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                            data-testid="checkout-address"
                            required />
                    </div>
                    <div class="mt-4 grid grid-cols-3 gap-4">
                        <div>
                            <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                                City
                            </label>
                            <input type="text" v-model="form.city"
                                class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                                data-testid="checkout-city"
                                required />
                        </div>
                        <div>
                            <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                                State/Province
                            </label>
                            <input type="text" v-model="form.state"
                                class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                                data-testid="checkout-state"
                                required />
                        </div>
                        <div>
                            <label class="block text-muted-foreground mb-2 font-semibold text-lg">
                                Postal Code
                            </label>
                            <input type="text" v-model="form.postalCode"
                                class="w-full p-3 border border-border rounded-lg bg-transparent text-foreground"
                                data-testid="checkout-postal-code"
                                required />
                        </div>
                    </div>

                    <p v-if="checkoutError" role="alert" class="mt-6 text-red-600">
                        {{ checkoutError }}
                    </p>
                    <div class="flex justify-end mt-6">
                        <button type="submit" :disabled="isSubmitting" :aria-busy="isSubmitting"
                            class="w-36 bg-primary text-primary-foreground p-3 rounded-lg hover:bg-primary/90 font-semibold text-lg tracking-wider">
                            Pay Now
                        </button>
                    </div>
                </form>
            </div>

            <!-- Right Column -->
            <div class="w-full px-8 lg:px-16 py-8 order-1 lg:order-2">
                <h2 class="text-2xl font-semibold">
                    Amount Due
                </h2>
                <div class="mt-8 lg:ps-12 divide-y-2 divide-brown overflow-auto">
                    <div v-for="product in cartProducts" :key="product.id"
                        class="flex items-center justify-between h-40 py-4 box-content">
                        <!-- Product Image -->
                        <img :src="product.gallery_urls[0]" alt="Product Image" class="w-28 lg:w-40 lg:h-full rounded" />
                        <div class="h-full relative flex-1 pl-4">
                            <div>
                                <!-- Product Title -->
                                <h3 class="font-semibold text-xl" v-if="currentLanguage === 'en'">
                                    {{ product.title }}
                                </h3>
                            </div>
                            <!-- Quantity -->
                            <p class="absolute bottom-0 text-md font-semibold">
                                Qty {{ product.quantity }}
                            </p>
                        </div>
                        <div class="text-right relative h-full grid">
                            <!-- Total Price -->
                            <p class="text-xl font-semibold">
                                ${{ product.price * product.quantity }}
                            </p>
                            <!-- Remove Product Button -->
                            <div class="flex items-end">
                                <a @click="removeProduct(product)" class="font-semibold text-lg">
                                    Remove
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-10 border-t-2 border-t-brown">
                    <div class="flex justify-between mt-4">
                        <span class="font-semibold text-2xl">Subtotal</span>
                        <span class="font-semibold text-2xl">$ {{ productStore.totalCartPrice }}</span>
                    </div>
                    <div class="flex justify-between mt-4">
                        <span class="font-semibold text-2xl">
                            Shipping
                        </span>
                        <span class="font-semibold text-2xl">$ {{ shippingCost }}</span>
                    </div>
                </div>

                <div class="mt-4 border-t-2 border-brown">
                    <div class="mt-4 flex justify-between font-semibold text-2xl">
                        <span>Total</span>
                        <span>$ {{ total }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="bg-primary text-primary-foreground p-4 text-start text-lg font-medium">
            © 2024 Senses Candles By Kate. All rights reserved.
        </div>
    </div>
</template>

<script setup>
    import { computed, reactive, ref, watchEffect, onMounted } from "vue";
    import { LockClosedIcon } from "@heroicons/vue/24/outline";
    import { useLanguageStore } from "@/stores/language.js";
    import { useProductStore } from "@/stores/product";
    import Swal from 'sweetalert2';
    import { useRouter } from 'vue-router';

    // Product store references
    const productStore = useProductStore();
    const cartProducts = computed(() => productStore.cartProducts);
    const shippingCost = ref(25.0);
    const total = computed(() => productStore.totalCartPrice + shippingCost.value);

    // Reactive references for language
    const languageStore = useLanguageStore();
    const currentLanguage = computed(() => languageStore.getCurrentLanguage);

    const router = useRouter();
    const isSubmitting = ref(false);
    const checkoutError = ref('');

    // Form reference
    const form = reactive({
        email: "",
        cardNumber: "",
        expirationDate: "",
        cvc: "",
        address: "",
        city: "",
        state: "",
        postalCode: "",
        soldProducts: "",
    });


    // It's necesary to activate overflow after Shopping Cart component
    onMounted(() => {
        document.body.style.overflow = 'auto'
    })

    /**
     * Handle form submission
     */
    const handleSubmit = async () => {
        if (isSubmitting.value) return;
        isSubmitting.value = true;
        checkoutError.value = '';
        form.soldProducts = extractProductInfo(cartProducts.value);

        try {
            const status = await productStore.createSale(form);
            if (status !== 201) throw new Error('Order creation was not confirmed');

            localStorage.removeItem("cartProducts");
            productStore.cartProducts = [];
            Swal.fire({
                title: currentLanguage.value === 'es'
                    ? 'Pedido creado correctamente'
                    : 'Order created successfully',
                icon: "success"
            });
            await router.push({ name: "home" });
        } catch {
            checkoutError.value = currentLanguage.value === 'es'
                ? 'No pudimos crear tu pedido. Conservamos tu carrito. Inténtalo de nuevo.'
                : 'We could not create your order. Your cart has been kept. Please try again.';
        } finally {
            isSubmitting.value = false;
        }
    };

    /**
     * Handle language change
     * @param {string} lang - Language to set
     */
    const handleLanguage = (lang) => {
        languageStore.setCurrentLanguage(lang);
    };

    /**
     * Extract specific fields from a list of products.
     *
     * @param {Array} products - The list of products to process.
     * @returns {Array} A new array of objects, where each object contains only the properties of each product.
     */
    const extractProductInfo = (products) => {
        return products.map((product) => ({
            product_id: product.id,
            quantity: product.quantity,
        }));
    };

    /**
     * Remove product from cart
     * @param {Number} productId - The ID of the product to remove
     */
    const removeProduct = (product) => {
        productStore.removeProductFromCart(product);
    };
</script>

<style scoped>
    body {
        font-family: "Arial", sans-serif;
    }
</style>