// vue component in pug
<template lang="pug">
div(style="height: 50px")
  button.border-0.flash-button.btn.h-100.w-100(
    disabled=false
    v-if="$store.getters.isLoading"
  )
    .d-flex.flex-row.justify-content-center.align-items-center
      span.spinner-border.spinner-border-sm
      .mx-2 {{$store.state.loadingMsg}}
</template>

<style scoped>
@keyframes glowing {
  0% {
    background-color: #bbb;
    box-shadow: 0 0 0;
    border: 0;
  }
  50% {
    background-color: #55b;
    box-shadow: 0 0 0;
    border: 0;
  }
  100% {
    background-color: #bbb;
    box-shadow: 0 0 0;
    border: 0;
  }
}

.flash-button {
  color: white;
  animation: glowing 2000ms infinite;
}
</style>
