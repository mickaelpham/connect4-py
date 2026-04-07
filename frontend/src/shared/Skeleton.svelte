<script lang='ts'>
  interface Props {
    width?: string
    height?: string
    borderRadius?: string
  }

  const { width = '100%', height = '1rem', borderRadius = '4px' }: Props = $props()
</script>

<div class='skeleton' style:width style:height style:border-radius={borderRadius}></div>

<style>
  .skeleton {
    background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
</style>
