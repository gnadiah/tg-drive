<script>
  import { onMount } from "svelte";
  import { auth } from "./stores/auth";
  import { logout } from "./lib/api";
  import Login from "./routes/Login.svelte";
  import Header from "./lib/components/Header.svelte";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import FileList from "./lib/components/FileList.svelte";
  import TransferManager from "./lib/components/TransferManager.svelte";
  import { Loader2 } from "lucide-svelte";

  let activeTab = "my-files";
  let searchQuery = "";

  onMount(() => {
    if (window.pywebview) {
      auth.check();
    } else {
      window.addEventListener("pywebviewready", () => {
        auth.check();
      });
    }
  });

  async function handleLogout() {
    try {
      await logout();
      auth.logout();
    } catch (err) {
      console.error("Logout failed:", err);
    }
  }
</script>

{#if $auth.loading}
  <div class="flex items-center justify-center h-screen">
    <Loader2 class="animate-spin text-primary" size={48} />
  </div>
{:else if $auth.error}
  <div class="flex flex-col items-center justify-center h-screen gap-4">
    <div class="text-destructive font-medium">Connection Error</div>
    <div class="text-sm text-muted-foreground">{$auth.error}</div>
    <button
      class="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm"
      on:click={() => auth.check()}
    >
      Retry
    </button>
  </div>
{:else if !$auth.isAuthenticated}
  <Login />
{:else}
  <div class="flex flex-col h-screen overflow-hidden">
    <Header
      bind:searchQuery
      on:logout={handleLogout}
      on:search={(e) => (searchQuery = e.detail)}
    />

    <div class="flex flex-1 overflow-hidden">
      <Sidebar {activeTab} on:change={(e) => (activeTab = e.detail)} />

      <main class="flex-1 overflow-hidden">
        {#if activeTab === "my-files"}
          <FileList {searchQuery} />
        {:else}
          <div
            class="flex items-center justify-center h-full text-muted-foreground"
          >
            <div class="text-center">
              <h3 class="text-lg font-medium mb-2">Coming Soon</h3>
              <p class="text-sm">
                The {activeTab.replace("-", " ")} view is under development.
              </p>
            </div>
          </div>
        {/if}
      </main>
    </div>

    <TransferManager />
  </div>
{/if}
