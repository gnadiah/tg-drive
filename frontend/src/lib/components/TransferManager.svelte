<script>
    import { fileStore } from "../../stores/files";
    import {
        Upload,
        Download,
        X,
        CheckCircle2,
        AlertCircle,
        Loader2,
        Minimize2,
        Maximize2,
    } from "lucide-svelte";
    import { slide } from "svelte/transition";
    import { cn } from "../../lib/utils";

    let expanded = true;

    $: uploads = Object.values($fileStore.uploads);
    $: downloads = Object.values($fileStore.downloads);
    $: transfers = [...uploads, ...downloads];
    $: hasTransfers = transfers.length > 0;
</script>

{#if hasTransfers}
    <div
        class="fixed bottom-6 right-6 w-80 bg-background border border-border rounded-[var(--radius-lg)] shadow-2xl overflow-hidden z-50 animate-in slide-in-from-bottom-10"
    >
        <!-- Header -->
        <div
            class="flex items-center justify-between p-3 bg-secondary/50 border-b border-border"
        >
            <div class="flex items-center gap-2">
                {#if uploads.length > 0}
                    <Upload size={14} class="text-primary" />
                {:else}
                    <Download size={14} class="text-primary" />
                {/if}
                <span class="text-sm font-medium">
                    {transfers.filter(
                        (t) =>
                            t.status === "uploading" ||
                            t.status === "downloading" ||
                            t.status === "processing",
                    ).length} active
                </span>
            </div>
            <div class="flex items-center gap-1">
                <button
                    on:click={() => (expanded = !expanded)}
                    class="p-1 hover:bg-background rounded-[var(--radius-sm)] transition-colors"
                >
                    {#if expanded}
                        <Minimize2 size={14} />
                    {:else}
                        <Maximize2 size={14} />
                    {/if}
                </button>
                <button
                    on:click={() => fileStore.clearCompleted()}
                    class="p-1 hover:bg-background rounded-[var(--radius-sm)] transition-colors"
                    title="Clear completed"
                >
                    <X size={14} />
                </button>
            </div>
        </div>

        <!-- List -->
        {#if expanded}
            <div
                class="max-h-64 overflow-y-auto p-2 space-y-2"
                transition:slide
            >
                {#each transfers as transfer (transfer.id)}
                    <div
                        class="p-3 bg-secondary/30 rounded-[var(--radius-md)] border border-border/50"
                    >
                        <div class="flex items-center justify-between mb-2">
                            <div
                                class="flex items-center gap-2 overflow-hidden"
                            >
                                {#if transfer.status === "uploading" || transfer.status === "processing"}
                                    <Upload
                                        size={14}
                                        class="text-muted-foreground shrink-0"
                                    />
                                {:else}
                                    <Download
                                        size={14}
                                        class="text-muted-foreground shrink-0"
                                    />
                                {/if}
                                <span
                                    class="text-sm font-medium truncate"
                                    title={transfer.file.name}
                                >
                                    {transfer.file.name}
                                </span>
                            </div>
                            <div class="shrink-0">
                                {#if transfer.status === "completed"}
                                    <CheckCircle2
                                        size={16}
                                        class="text-green-500"
                                    />
                                {:else if transfer.status === "error"}
                                    <AlertCircle
                                        size={16}
                                        class="text-destructive"
                                    />
                                {:else if transfer.status === "processing"}
                                    <Loader2
                                        size={16}
                                        class="animate-spin text-yellow-500"
                                    />
                                {:else}
                                    <div class="flex flex-col items-end">
                                        <span
                                            class="text-xs text-muted-foreground"
                                            >{transfer.progress}%</span
                                        >
                                        {#if transfer.speed}
                                            <span
                                                class="text-[10px] text-muted-foreground/70"
                                                >{transfer.speed}</span
                                            >
                                        {/if}
                                    </div>
                                {/if}
                            </div>
                        </div>

                        <!-- Progress Bar -->
                        {#if transfer.status !== "error"}
                            <div
                                class="h-1.5 w-full bg-secondary rounded-full overflow-hidden"
                            >
                                <div
                                    class={cn(
                                        "h-full transition-all duration-300",
                                        transfer.status === "completed"
                                            ? "bg-green-500"
                                            : transfer.status === "processing"
                                              ? "bg-yellow-500 animate-pulse"
                                              : "bg-primary",
                                    )}
                                    style="width: {transfer.progress}%"
                                ></div>
                            </div>
                        {/if}

                        <!-- Status Text -->
                        <div class="flex justify-between mt-1.5">
                            <span
                                class="text-[10px] text-muted-foreground uppercase tracking-wider"
                            >
                                {transfer.status}
                            </span>
                            {#if transfer.error}
                                <span
                                    class="text-[10px] text-destructive truncate max-w-[150px]"
                                    title={transfer.error}
                                >
                                    {transfer.error}
                                </span>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
{/if}
