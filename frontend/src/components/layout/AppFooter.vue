<template>
  <footer class="bg-white border-t border-surface-200 mt-auto">
    <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 py-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 17h8M8 17v-4m8 4v-4m-8 0h8m-8 0V9m8 4V9M4 21h16a1 1 0 001-1V8l-3-4H6L3 8v12a1 1 0 001 1z" />
              </svg>
            </div>
            <span class="text-lg font-bold text-primary-500">FleetLease</span>
          </div>
          <p class="text-sm text-gray-500">
            Платформа лизинга грузовой техники. Связываем лизингополучателей, лизингодателей и поставщиков.
          </p>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-gray-800 mb-3">Навигация</h4>
          <div class="flex flex-col gap-2">
            <router-link to="/" class="text-sm text-gray-500 hover:text-primary-500 transition-colors">Каталог техники</router-link>
            <router-link to="/suppliers" class="text-sm text-gray-500 hover:text-primary-500 transition-colors">Поставщики</router-link>
            <router-link to="/lessors" class="text-sm text-gray-500 hover:text-primary-500 transition-colors">Лизингодатели</router-link>
          </div>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-gray-800 mb-3">Контакты</h4>
          <div class="flex flex-col gap-2 text-sm text-gray-500">
            <span>+375 (29) 000-00-00</span>
            <span>info@fleetlease.by</span>
            <span>г. Минск, Республика Беларусь</span>
          </div>
        </div>
      </div>
      <div class="border-t border-surface-200 mt-8 pt-6 text-center text-xs text-gray-400">
        &copy; {{ new Date().getFullYear() }} FleetLease. Все права защищены.
      </div>
    </div>
  </footer>
</template>
