<script>
    import { HardDrive, Clock, Star, Trash2, Cloud } from "lucide-svelte";
    import { createEventDispatcher } from "svelte";
    import { cn } from "../utils";

    export let activeTab = "my-files";
    const dispatch = createEventDispatcher();

    const menuItems = [
        { id: "my-files", label: "My Files", icon: HardDrive },
        { id: "recent", label: "Recent", icon: Clock },
        { id: "starred", label: "Starred", icon: Star },
        { id: "trash", label: "Trash", icon: Trash2 },
    ];
</script>

<aside class="w-64 border-r border-border flex flex-col h-full bg-background">
    <div class="p-6">
        <div class="flex items-center gap-3 mb-6">
            <div
                class="w-9 h-9 bg-gradient-to-br from-primary to-primary/80 rounded-[var(--radius-md)] flex items-center justify-center text-white shadow-md"
            >
                <Cloud size={20} strokeWidth={2.5} />
            </div>
            <span class="text-lg font-semibold tracking-tight">TG Drive</span>
        </div>

        <nav class="space-y-1">
            {#each menuItems as item}
                <button
                    on:click={() => dispatch("change", item.id)}
                    class={cn(
                        "w-full flex items-center gap-3 px-4 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-all",
                        activeTab === item.id
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                    )}
                >
                    <svelte:component
                        this={item.icon}
                        size={20}
                        strokeWidth={activeTab === item.id ? 2.5 : 2}
                    />
                    {item.label}
                </button>
            {/each}
        </nav>
    </div>
</aside>
