<template>
    <!-- Product Section -->
    <div v-if="product" class="relative isolate px-6 lg:px-8">
        <div class="bg-background">
            <div class="mx-auto max-w-2xl px-4 py-16 sm:px-6 sm:py-6 lg:max-w-7xl lg:px-8">
                <div class="lg:grid lg:grid-cols-2 lg:items-start lg:gap-x-8">

                    <!-- Image Gallery -->
                    <TabGroup as="div" class="flex flex-col-reverse">

                        <!-- Image Selector -->
                        <div class="mx-auto mt-6 w-full max-w-2xl lg:max-w-none">
                            <TabList class="grid grid-cols-4 gap-6">
                                <Tab v-for="(image, index) in product.gallery_urls" :key="image"
                                    :aria-label="`View image ${index + 1}`"
                                    class="relative flex h-24 cursor-pointer items-center justify-center rounded-md bg-card text-sm font-medium uppercase hover:bg-muted transition-transform duration-300 transform hover:scale-110">
                                    <span class="absolute inset-0 overflow-hidden rounded-md">
                                        <img :src="image" alt="" class="h-full w-full object-cover object-center" />
                                    </span>
                                    <span
                                        :class="[selected ? 'ring-foreground' : 'ring-transparent', 'pointer-events-none absolute inset-0 rounded-md ring-2 ring-offset-2']"
                                        aria-hidden="true" />
                                </Tab>
                            </TabList>
                        </div>

                        <TabPanels class="aspect-h-1 aspect-w-1 w-full">
                            <TabPanel v-for="image in product.gallery_urls" :key="image">
                                <img :src="image" alt="" class="h-full w-full object-cover object-center sm:rounded-lg"
                                    @mousemove="handleMouseMove" 
                                    @mouseenter="handleMouseEnter(image)"
                                    @mouseleave="handleMouseLeave" />
                            </TabPanel>
                        </TabPanels>
                    </TabGroup>

                    <!-- Product Info -->
                    <div v-if="selectedImage" class="mt-10 px-4 sm:mt-16 sm:px-0 lg:mt-0">
                        <div class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-lg">
                            <img :src="selectedImage" alt="" class="h-full w-full object-cover"
                                :style="{ transform: `scale(${4}) translate(${mouseX}px, ${mouseY}px)` }" />
                        </div>
                    </div>

                    <div v-if="!selectedImage" class="mt-10 px-4 sm:mt-16 sm:px-0 lg:mt-0">

                        <!-- Product Title and Price -->
                        <div class="mt-3 flex justify-between">
                            <h1 v-if="currentLanguage === 'en'"
                                class="inline-block text-3xl font-semibold tracking-tight">
                                {{ product.title }}
                            </h1>
                            <p class="inline-block text-3xl tracking-tight">
                                $ {{ product.price }}
                            </p>
                        </div>

                        <!-- Introductory phrase of the product -->
                        <div class="mt-8">
                            <p class="font-medium text-lg ">
                                <span v-if="currentLanguage === 'en'">
                                    {{ product.description }}
                                </span>
                            </p>
                        </div>

                        <!-- Quantity Selector and Add to Cart Button -->
                        <div class="flex items-center gap-4 mt-12">
                            <div class="flex items-center border border-border rounded-full h-12">
                                <button
                                    class="px-3 py-2 hover:text-muted-foreground"
                                    data-testid="quantity-decrement"
                                    @click="decrementQuantity">
                                    <MinusSmallIcon class="h-6 w-6" aria-hidden="true" />
                                </button>
                                <span data-testid="quantity-value" class="px-4 py-2 font-semibold">{{ productQuantity }}</span>
                                <button
                                    class="px-3 py-2 hover:text-muted-foreground"
                                    data-testid="quantity-increment"
                                    @click="productQuantity++">
                                    <PlusSmallIcon class="w-6 h-6"/>
                                </button>
                                
                            </div>

                            <button data-testid="add-to-cart" @click="addToCart"
                                class="px-8 py-2 w-full h-12 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 text-md">
                                <span class="uppercase">Add to cart</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Trending Products Carousel -->
    <div class="mx-auto flex flex-col items-center justify-center max-w-7xl px-8 py-12">
        <h2 class="uppercase pb-4 tracking-widest text-center text-2xl">
            Trending Products
        </h2>
        <ProductCarousel :top="top_products"></ProductCarousel>
    </div>
</template>

<script setup>
    import { computed, onMounted, ref } from 'vue';
    import { useRoute } from 'vue-router';
    import Swal from 'sweetalert2';
    import {
        Tab, TabGroup, TabList, TabPanel, TabPanels,
    } from '@headlessui/vue';
    import { MinusSmallIcon, PlusSmallIcon } from '@heroicons/vue/24/outline';
    import ProductCarousel from "@/components/product/ProductCarousel.vue";
    import { useLanguageStore } from '@/stores/language.js';
    import { useProductStore } from '@/stores/product';
    import { initModals } from 'flowbite';

    // Initialize stores and references
    const languageStore = useLanguageStore();
    const productStore = useProductStore();
    const currentLanguage = computed(() => languageStore.getCurrentLanguage);

    const productQuantity = ref(1);
    const selected = '';
    const selectedImage = ref(null);
    const mouseX = ref(0);
    const mouseY = ref(0);
    const zoom = ref(2);

    const route = useRoute();
    const productId = ref(0);
    const product = computed(() => productStore.productById(productId.value));

    const top_products = ref(null);
    if (window.innerWidth >= 1024) {
        top_products.value = 4;
    } else if (window.innerWidth < 1024 && 760 <= window.innerWidth) {
        top_products.value = 2;
    } else if (window.innerWidth < 760) {
        top_products.value = 1;
    }

    /**
     * onMounted lifecycle hook.
     * Fetches product data and initializes modals.
     */
    onMounted(async () => {
        window.scrollTo({ top: 0 });
        productId.value = parseInt(route.params.product_id);
        await productStore.fetchProducts();
        initModals();
    });

    /**
     * Decrease the product quantity by 1.
     */
    const decrementQuantity = () => {
        if (productQuantity.value > 1) {
            productQuantity.value--;
        }
    };

    /**
     * Add product to the shopping cart.
     */
    const addToCart = () => {
        productStore.addProductToCart(product.value, productQuantity.value);
        Swal.fire({
            title: "Product added to Shopping Cart successfully",
            icon: "success"
        });
    };

    /**
     * Handle mouse enter event on image.
     * @param {string} image - The image URL.
     */
    const handleMouseEnter = (image) => {
        selectedImage.value = image;
    };

    /**
     * Handle mouse leave event.
     */
    const handleMouseLeave = () => {
        selectedImage.value = null;
        resetZoom();
    };

    /**
     * Handle mouse move event for image zoom effect.
     * @param {Event} event - Mouse move event.
     */
    const handleMouseMove = (event) => {
        if (!selectedImage.value) return;
        const img = event.target.getBoundingClientRect();
        mouseX.value = (event.clientX - img.left - (img.width / 2)) * -1;
        mouseY.value = (event.clientY - img.top - (img.height / 2)) * -1;
        zoom.value = 2;
    };

    /**
     * Reset zoom effect.
     */
    const resetZoom = () => {
        mouseX.value = 0;
        mouseY.value = 0;
        zoom.value = 2;
    };
</script>