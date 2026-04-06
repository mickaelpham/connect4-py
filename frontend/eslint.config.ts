import antfu from '@antfu/eslint-config'

export default antfu({
  svelte: true,
  typescript: {
    tsconfigPath: './tsconfig.app.json',
  },
}, {
  files: ['**/*.test.ts'],
  rules: {
    'ts/no-unsafe-call': 'off',
    'ts/no-unsafe-member-access': 'off',
  },
})
