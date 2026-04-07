<script lang='ts'>
  import { dismissToast, getToasts } from './toast.svelte'

  const store = getToasts()
</script>

{#if store.list.length > 0}
  <div class='toast-container'>
    {#each store.list as toast (toast.id)}
      <div class='toast {toast.level}'>
        <span class='toast-message'>{toast.message}</span>
        <button class='toast-dismiss' onclick={() => dismissToast(toast.id)} aria-label='Dismiss'>
          &times;
        </button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 380px;
  }

  .toast {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: slide-in 0.2s ease-out;
  }

  .toast.error {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  .toast.warning {
    background: #fffbeb;
    color: #92400e;
    border: 1px solid #fed7aa;
  }

  .toast-message {
    flex: 1;
    line-height: 1.4;
  }

  .toast-dismiss {
    background: none;
    border: none;
    font-size: 1.25rem;
    line-height: 1;
    cursor: pointer;
    color: inherit;
    opacity: 0.6;
    padding: 0;
    flex-shrink: 0;
  }

  .toast-dismiss:hover {
    opacity: 1;
  }

  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
</style>
