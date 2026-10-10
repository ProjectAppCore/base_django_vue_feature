<template>
    <!-- Responsive grid of trending products. Component name is kept for existing imports. -->
    <div v-if="productsOnTrending && productsOnTrending.length" class="carousel-container w-full py-16">
        <div class="text-center mb-8">
            <h2 class="text-3xl font-semibold">TRENDING NOW</h2>
            <p class="text-xl font-medium text-muted-foreground">
                Discover the trending products. Explore now |
                <RouterLink :to="{ name: 'catalog'}">
                    <span class="border-b-2 border-b-muted-foreground">SHOP NOW</span>
                </RouterLink>
            </p>
        </div>
        <ul class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5" data-testid="product-carousel-list">
            <li v-for="product in productsOnTrending" :key="product.id" class="min-w-0">
                <router-link :to="{ name: 'product', params: { product_id: product.id } }"
                    class="block px-2 cursor-pointer" data-testid="product-carousel-item">
                    <div class="shadow">
                        <img :src="product.gallery_urls[0]" :alt="product.title"
                            class="w-full object-cover mb-4" />
                        <div class="text-center">
                            <h3 class="text-lg font-semibold">
                                <!-- Display product name based on current language -->
                                <span v-if="currentLanguage === 'en'">{{ product.title }}</span>
                            </h3>
                            <p class="text-lg font-semibold">
                                ${{ product.price }}
                            </p>
                        </div>
                    </div>
                </router-link>
            </li>
        </ul>
    </div>
</template>

<script setup>
    // Importing necessary modules
    import { computed, ref, onMounted } from "vue";
    import { useLanguageStore } from '@/stores/language.js';
    import { useProductStore } from "@/stores/product";

    // Initializing state
    const productsOnTrending = ref(null);

    // Access the current language from the store
    const appStore = useLanguageStore();
    const currentLanguage = computed(() => appStore.getCurrentLanguage);

    // Access the product store to get trending products
    const productStore = useProductStore();

    // Fetch products when the component is mounted
    onMounted(async () => {
        await productStore.fetchProducts();
        productsOnTrending.value = productStore.products;
    });

</script>
