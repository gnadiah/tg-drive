<script lang="ts">
    import { X } from "lucide-svelte";
    import { createEventDispatcher } from "svelte";
    import { cn } from "../utils";

    export let open: boolean = false;
    export let title: string = "";
    export let message: string = "";
    export let type: "confirm" | "prompt" = "confirm";
    export let value: string = "";
    export let confirmText: string = "Confirm";
    export let cancelText: string = "Cancel";
    export let destructive: boolean = false;
    export let maxWidth: string = "max-w-md";

    // Declare that this component accepts slot content
    interface $$Slots {
        default: {};
    }

    const dispatch = createEventDispatcher();

    function handleConfirm() {
        dispatch("confirm", type === "prompt" ? value : true);
        open = false;
    }

    function handleCancel() {
        dispatch("cancel");
        open = false;
    }

    function handleBackdropClick(e) {
        if (e.target === e.currentTarget) {
            handleCancel();
        }
    }
</script>

{#if open}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
        on:click={handleBackdropClick}
        on:keydown={(e) => e.key === "Escape" && handleCancel()}
        role="button"
        tabindex="-1"
    >
        <!-- Dialog -->
        <div
            class={cn(
                "bg-background border border-border shadow-lg rounded-[var(--radius-lg)] p-6 w-full animate-in zoom-in-95 duration-200",
                maxWidth,
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby="dialog-title"
        >
            <slot>
                <!-- Default content when no slot is provided -->
                <!-- Header -->
                <div class="flex items-start justify-between mb-4">
                    <h2 id="dialog-title" class="text-lg font-semibold">
                        {title}
                    </h2>
                    <button
                        on:click={handleCancel}
                        class="p-1 hover:bg-secondary rounded-[var(--radius-sm)] transition-colors"
                        aria-label="Close"
                    >
                        <X size={20} class="text-muted-foreground" />
                    </button>
                </div>

                <!-- Content -->
                <div class="mb-6">
                    {#if message}
                        <p class="text-sm text-muted-foreground mb-4">
                            {message}
                        </p>
                    {/if}

                    {#if type === "prompt"}
                        <input
                            type="text"
                            bind:value
                            class="w-full px-3 py-2 bg-secondary/50 border border-border rounded-[var(--radius-md)] text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                            placeholder="Enter value..."
                            on:keydown={(e) =>
                                e.key === "Enter" && handleConfirm()}
                        />
                    {/if}
                </div>

                <!-- Actions -->
                <div class="flex gap-2 justify-end">
                    <button
                        on:click={handleCancel}
                        class="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground rounded-[var(--radius-md)] text-sm font-medium transition-colors"
                    >
                        {cancelText}
                    </button>
                    <button
                        on:click={handleConfirm}
                        class={cn(
                            "px-4 py-2 rounded-[var(--radius-md)] text-sm font-medium transition-colors shadow-sm",
                            destructive
                                ? "bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                                : "bg-primary hover:opacity-90 text-primary-foreground",
                        )}
                    >
                        {confirmText}
                    </button>
                </div>
            </slot>
        </div>
    </div>
{/if}

<style>
    @keyframes fade-in {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    @keyframes zoom-in-95 {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    .animate-in {
        animation-fill-mode: both;
    }

    .fade-in {
        animation-name: fade-in;
    }

    .zoom-in-95 {
        animation-name: zoom-in-95;
    }

    .duration-200 {
        animation-duration: 200ms;
    }
</style>
