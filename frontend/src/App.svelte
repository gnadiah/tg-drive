<script>
  import { onMount } from "svelte";
  import { auth } from "./stores/auth";
  import { passcode } from "./stores/passcode";
  import { logout } from "./lib/api";
  import Login from "./routes/Login.svelte";
  import PasscodeSetup from "./lib/components/PasscodeSetup.svelte";
  import PasscodeDialog from "./lib/components/PasscodeDialog.svelte";
  import ForgotPasscodeDialog from "./lib/components/ForgotPasscodeDialog.svelte";
  import ChangePasscodeDialog from "./lib/components/ChangePasscodeDialog.svelte";
  import Header from "./lib/components/Header.svelte";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import FileList from "./lib/components/FileList.svelte";
  import TransferManager from "./lib/components/TransferManager.svelte";
  import { Loader2 } from "lucide-svelte";

  let activeTab = "my-files";
  let searchQuery = "";
  let showForgotDialog = false;
  let showChangePasscodeDialog = false;
  let hasCheckedPasscode = false; // Prevent infinite passcode.check() loop

  function handleChangePasscode() {
    showChangePasscodeDialog = true;
  }

  function handleChangeSuccess() {
    // Optional: Show toast notification
    console.log("Passcode changed successfully");
  }

  onMount(() => {
    if (window.pywebview) {
      auth.check();
    } else {
      window.addEventListener("pywebviewready", () => {
        auth.check();
      });
    }
  });

  // Check passcode ONCE after authentication
  $: if (
    $auth.isAuthenticated &&
    !hasCheckedPasscode &&
    !$passcode.isVerified
  ) {
    hasCheckedPasscode = true;
    passcode.check();
  }

  // Reset guard on logout
  $: if (!$auth.isAuthenticated) {
    hasCheckedPasscode = false;
  }

  async function handleLogout() {
    try {
      await logout();
      auth.logout();
      passcode.resetState();
    } catch (err) {
      console.error("Logout failed:", err);
    }
  }

  async function handlePasscodeSetup(event) {
    const result = await passcode.setup(event.detail);
    if (!result.success) {
      console.error("Passcode setup failed:", result.error);
    }
  }

  function handlePasscodeSkip() {
    passcode.skip();
  }

  async function handlePasscodeVerify(event) {
    await passcode.verify(event.detail);
  }

  function handleForgot() {
    showForgotDialog = true;
  }

  async function handleResetConfirm() {
    const result = await passcode.reset();
    if (result.success) {
      showForgotDialog = false;
      hasCheckedPasscode = false; // Allow re-check after reset
      passcode.check();
    }
  }

  function handleUnlocked() {
    passcode.clearError();
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
{:else if $passcode.isLoading}
  <div class="flex items-center justify-center h-screen">
    <Loader2 class="animate-spin text-primary" size={48} />
  </div>
{:else if !$passcode.hasPasscode && !$passcode.isVerified}
  <!-- First time: show passcode setup -->
  <PasscodeSetup
    on:complete={handlePasscodeSetup}
    on:skip={handlePasscodeSkip}
  />
{:else if $passcode.hasPasscode && !$passcode.isVerified}
  <!-- Has passcode: show verification dialog -->
  <PasscodeDialog
    title="Enter Passcode"
    error={$passcode.error}
    attemptsRemaining={$passcode.attemptsRemaining}
    lockedUntil={$passcode.lockedUntil}
    loading={$passcode.isLoading}
    on:submit={handlePasscodeVerify}
    on:forgot={handleForgot}
    on:unlocked={handleUnlocked}
  />

  <!-- Forgot Passcode Dialog -->
  <ForgotPasscodeDialog
    bind:open={showForgotDialog}
    on:confirm={handleResetConfirm}
  />
{:else}
  <!-- Authenticated AND passcode verified: show main app -->
  <div class="flex flex-col h-screen overflow-hidden">
    <Header
      bind:searchQuery
      on:logout={handleLogout}
      on:changePasscode={handleChangePasscode}
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

    <ChangePasscodeDialog
      bind:open={showChangePasscodeDialog}
      on:success={handleChangeSuccess}
    />
  </div>
{/if}
