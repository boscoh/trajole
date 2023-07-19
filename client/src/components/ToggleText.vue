// vue component in pug
<template lang="pug">
  button.btn.btn-sm.btn-secondary(@click="submit")
    span
      span(v-if="flag")
        slot
        =" "
        i.fas.fa-check
      template(v-else)
        slot
</template>

<script>
export default {
  props: ["flag"],
  methods: {
    submit() {
      this.$emit("click");
    },
  },
};
</script>
