// vite.config.js
const { createVuePlugin } = require('vite-plugin-vue2')

export default {
  plugins: [createVuePlugin()],
  server: {
    port: 3333
  },
  base: './'
}
