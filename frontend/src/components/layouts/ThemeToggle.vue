<!--
  ThemeToggle — three-state theme switcher (Light / Dark / System).
  Uses the `theme` Pinia store. Renders a Headless UI menu so it stays
  accessible (keyboard nav, focus trap, aria attributes).
-->
<template>
  <Menu as="div" class="relative">
    <MenuButton
      aria-label="Toggle theme"
      class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-foreground hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors"
    >
      <component :is="currentIcon" class="h-5 w-5" />
    </MenuButton>
    <MenuItems
      class="absolute right-0 z-50 mt-2 w-36 origin-top-right overflow-hidden rounded-md border border-border bg-popover text-popover-foreground shadow-lg focus:outline-none"
    >
      <MenuItem v-for="opt in OPTIONS" :key="opt.value" v-slot="{ active }">
        <button
          type="button"
          @click="themeStore.setMode(opt.value)"
          :class="[
            'flex min-h-11 w-full items-center gap-2 px-3 py-2 text-sm',
            active ? 'bg-accent text-accent-foreground' : '',
            themeStore.mode === opt.value ? 'text-primary font-medium' : '',
          ]"
        >
          <component :is="opt.Icon" class="h-4 w-4" />
          {{ opt.label }}
        </button>
      </MenuItem>
    </MenuItems>
  </Menu>
</template>

<script setup>
import { computed } from 'vue';
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/vue/24/outline';
import { useThemeStore } from '@/stores/theme';

const themeStore = useThemeStore();

const OPTIONS = [
  { value: 'light', label: 'Light', Icon: SunIcon },
  { value: 'dark', label: 'Dark', Icon: MoonIcon },
  { value: 'system', label: 'System', Icon: ComputerDesktopIcon },
];

const currentIcon = computed(() => {
  const found = OPTIONS.find((o) => o.value === themeStore.mode);
  return found ? found.Icon : ComputerDesktopIcon;
});
</script>
