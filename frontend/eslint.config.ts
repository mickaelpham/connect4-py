import antfu from '@antfu/eslint-config'

export default antfu({
  svelte: true,
  typescript: {
    tsconfigPath: './tsconfig.app.json',
  },
})
