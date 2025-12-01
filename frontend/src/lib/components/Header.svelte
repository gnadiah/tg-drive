<script>
    import { Search, User, LogOut, Lock } from "lucide-svelte";
    import { createEventDispatcher } from "svelte";

    const dispatch = createEventDispatcher();

    export let searchQuery = "";

    let showUserMenu = false;

    function handleSearchInput(e) {
        const target = e.target;
        if (target instanceof HTMLInputElement) {
            dispatch("search", target.value);
        }
    }

    function handleClickOutside(e) {
        const target = e.target;
        if (target instanceof Element && !target.closest("button")) {
            showUserMenu = false;
        }
    }
</script>

<header
    class="h-16 border-b border-border px-6 flex items-center justify-between bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 relative z-50"
>
    <div class="flex-1 max-w-xl">
        <div class="relative">
            <Search
                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                size={18}
            />
            <input
                type="text"
                bind:value={searchQuery}
                on:input={handleSearchInput}
                placeholder="Search files..."
                class="h-10 w-full rounded-[var(--radius-md)] border border-input bg-background pl-11 pr-4 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
        </div>
    </div>

    <div class="relative">
        <button
            on:click={() => (showUserMenu = !showUserMenu)}
            class="flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] hover:bg-secondary transition-colors"
        >
            <div
                class="w-8 h-8 bg-gradient-to-br from-primary/20 to-primary/10 rounded-full flex items-center justify-center"
            >
                <User size={18} class="text-primary" />
            </div>
        </button>

        {#if showUserMenu}
            <div
                class="absolute right-0 mt-2 w-48 bg-background border border-border rounded-[var(--radius-md)] shadow-lg py-1 z-[100]"
            >
                <button
                    on:click={() => dispatch("changePasscode")}
                    class="w-full flex items-center gap-3 px-4 py-2 text-sm hover:bg-secondary transition-colors"
                >
                    <Lock size={16} />
                    Change Passcode
                </button>
                <div class="h-px bg-border my-1"></div>
                <button
                    on:click={() => dispatch("logout")}
                    class="w-full flex items-center gap-3 px-4 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                >
                    <LogOut size={16} />
                    Logout
                </button>
            </div>
        {/if}
    </div>
</header>

<svelte:window on:click={handleClickOutside} />
