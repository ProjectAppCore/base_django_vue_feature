<template>
    <header class="bg-card shadow-sm sticky top-0 z-50">
        <!-- Navbar for large screens -->
        <nav class="mx-auto flex max-w-7xl items-center justify-between gap-2 p-4 lg:px-8" aria-label="Global">
            <!-- Logo/Brand -->
            <div class="flex min-w-0 flex-1">
                <router-link to="/" class="max-w-40 truncate text-xl font-bold text-foreground lg:max-w-none">
                    Base Project
                </router-link>
            </div>

            <!-- Desktop Navigation Links -->
            <div class="hidden lg:flex lg:gap-x-8">
                <router-link to="/" class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                    Home
                </router-link>
                <router-link to="/blogs" class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                    Blogs
                </router-link>
                <router-link to="/catalog" class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                    Catalog
                </router-link>
                <router-link to="/manual" class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                    Manual
                </router-link>
                <router-link to="/about_us" class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                    About Us
                </router-link>
                <router-link to="/contact" class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                    Contact
                </router-link>
            </div>

            <!-- Right side actions -->
            <div class="flex shrink-0 items-center gap-2 lg:flex-1 lg:justify-end lg:gap-x-4">
                <!-- Search icon -->
                <button @click="showSearchBar = true" aria-label="Search products" class="flex h-11 w-11 shrink-0 items-center justify-center hover:bg-accent rounded-full" data-testid="header-search">
                    <MagnifyingGlassIcon class="h-6 w-6 text-foreground" />
                </button>

                <!-- Shopping cart -->
                <button @click="showShoppingCart = true" aria-label="Open shopping cart" class="relative flex h-11 w-11 shrink-0 items-center justify-center hover:bg-accent rounded-full" data-testid="header-cart">
                    <ShoppingBagIcon class="h-6 w-6 text-foreground" />
                    <span v-if="totalCartProducts > 0"
                        class="absolute -top-1 -right-1 bg-destructive text-destructive-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        {{ totalCartProducts }}
                    </span>
                </button>

                <!-- Theme toggle -->
                <ThemeToggle />

                <!-- Desktop auth buttons; mobile auth stays in the menu. -->
                <div class="hidden lg:flex lg:items-center lg:gap-x-4">
                    <template v-if="isAuthenticated">
                        <router-link to="/dashboard"
                            class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                            Dashboard
                        </router-link>
                        <button @click="handleSignOut" data-testid="header-sign-out"
                            class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                            Sign Out
                        </button>
                    </template>
                    <template v-else>
                        <router-link to="/sign_in"
                            class="text-sm font-semibold leading-6 text-foreground hover:text-muted-foreground">
                            Sign In
                        </router-link>
                        <router-link to="/sign_up"
                            class="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90">
                            Sign Up
                        </router-link>
                    </template>
                </div>
            </div>

            <!-- Mobile menu button -->
            <div class="flex shrink-0 lg:hidden">
                <button type="button" @click="mobileMenuOpen = true"
                    class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-md p-2.5 text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                    <span class="sr-only">Open main menu</span>
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round"
                            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                    </svg>
                </button>
            </div>
        </nav>

        <!-- Mobile menu -->
        <div v-if="mobileMenuOpen" class="lg:hidden" role="dialog" aria-modal="true">
            <div class="fixed inset-0 z-50"></div>
            <div
                class="fixed inset-y-0 right-0 z-50 w-full overflow-y-auto bg-card px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-border">
                <div class="flex items-center justify-between">
                    <router-link to="/" class="text-xl font-bold text-foreground" @click="mobileMenuOpen = false">
                        Base Project
                    </router-link>
                    <button type="button" @click="mobileMenuOpen = false" class="-m-2.5 rounded-md p-2.5 text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                        <span class="sr-only">Close menu</span>
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <div class="mt-6 flow-root">
                    <div class="-my-6 divide-y divide-border">
                        <div class="space-y-2 py-6">
                            <router-link to="/" @click="mobileMenuOpen = false"
                                class="block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                Home
                            </router-link>
                            <router-link to="/blogs" @click="mobileMenuOpen = false"
                                class="block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                Blogs
                            </router-link>
                            <router-link to="/catalog" @click="mobileMenuOpen = false"
                                class="block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                Catalog
                            </router-link>
                            <router-link to="/manual" @click="mobileMenuOpen = false"
                                class="block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                Manual
                            </router-link>
                            <router-link to="/about_us" @click="mobileMenuOpen = false"
                                class="block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                About Us
                            </router-link>
                            <router-link to="/contact" @click="mobileMenuOpen = false"
                                class="block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                Contact
                            </router-link>
                        </div>
                        <div class="py-6">
                            <template v-if="isAuthenticated">
                                <router-link to="/dashboard" @click="mobileMenuOpen = false"
                                    class="block rounded-lg px-3 py-2.5 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                    Dashboard
                                </router-link>
                                <button @click="handleSignOut" data-testid="mobile-sign-out"
                                    class="block w-full text-left rounded-lg px-3 py-2.5 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                    Sign Out
                                </button>
                            </template>
                            <template v-else>
                                <router-link to="/sign_in" @click="mobileMenuOpen = false"
                                    class="block rounded-lg px-3 py-2.5 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                    Sign In
                                </router-link>
                                <router-link to="/sign_up" @click="mobileMenuOpen = false"
                                    class="block rounded-lg px-3 py-2.5 text-base font-semibold leading-7 text-foreground hover:bg-muted">
                                    Sign Up
                                </router-link>
                            </template>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Search bar component -->
        <div v-if="showSearchBar" class="fixed z-30 top-0">
            <SearchBar :visible="showSearchBar" @update:visible="showSearchBar = $event"></SearchBar>
        </div>

        <!-- Shopping cart component -->
        <ShoppingCart :visible="showShoppingCart" @update:visible="showShoppingCart = $event" />
    </header>
</template>

<script setup>
    import { computed, ref } from "vue";
    import { useRouter } from "vue-router";
    import { MagnifyingGlassIcon, ShoppingBagIcon } from '@heroicons/vue/24/outline';
    import SearchBar from "@/components/layouts/SearchBar.vue";
    import ShoppingCart from "@/components/product/ShoppingCart.vue";
    import ThemeToggle from "@/components/layouts/ThemeToggle.vue";
    import { useAuthStore } from "@/stores/auth";
    import { useProductStore } from "@/stores/product";

    const router = useRouter();
    const authStore = useAuthStore();
    const productStore = useProductStore();

    // Reactive references
    const showSearchBar = ref(false);
    const showShoppingCart = ref(false);
    const mobileMenuOpen = ref(false);

    const totalCartProducts = computed(() => productStore.totalCartProducts);
    const isAuthenticated = computed(() => authStore.token && authStore.user?.id);

    const handleSignOut = () => {
        authStore.logout();
        mobileMenuOpen.value = false;
        router.push('/');
    };
</script>
