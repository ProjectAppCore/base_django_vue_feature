<template>
    <!-- Responsive grid of trending blogs. Component name is kept for existing imports. -->
    <div v-if="blogsOnTrending && blogsOnTrending.length" class="carousel-container w-full p-16">
        <div class="text-center mb-8">
            <h2 class="text-3xl font-semibold">TRENDING NOW</h2>
            <p class="text-xl font-medium text-muted-foreground">
                Discover the trending blogs. |
                <RouterLink :to="{ name: 'blogs'}">
                    <span class="border-b-2 border-b-muted-foreground">Explore now</span>
                </RouterLink>
            </p>
        </div>
        <ul class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5" data-testid="blog-carousel-list">
            <li v-for="blog in blogsOnTrending" :key="blog.id" class="min-w-0">
                <router-link :to="{ name: 'blog', params: { blog_id: blog.id } }"
                    class="block px-2 cursor-pointer" data-testid="blog-carousel-item">
                    <div class="shadow">
                        <img :src="blog.image_url" :alt="blog.title"
                            class="w-full object-cover mb-4" />
                        <div class="text-center">
                            <h3 class="text-lg font-semibold">
                                <!-- Display blog name based on current language -->
                                <span v-if="currentLanguage === 'en'">{{ blog.title }}</span>
                            </h3>
                            <p class="text-lg font-semibold">
                                {{ blog.category }}
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
    import { useBlogStore } from "@/stores/blog";

    // Initializing state
    const blogsOnTrending = ref(null);

    // Access the current language from the store
    const appStore = useLanguageStore();
    const currentLanguage = computed(() => appStore.getCurrentLanguage);

    // Access the blog store to get trending blogs
    const blogStore = useBlogStore();

    // Fetch blogs when the component is mounted
    onMounted(async () => {
        await blogStore.fetchBlogs();
        blogsOnTrending.value = blogStore.blogs;
    });

</script>
