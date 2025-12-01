<script>
    import { createEventDispatcher } from "svelte";
    import { Lock, ArrowRight, Check, X } from "lucide-svelte";
    import { passcode } from "../../stores/passcode";

    const dispatch = createEventDispatcher();

    export let open = false;

    let step = 1; // 1: Old, 2: New, 3: Confirm
    let oldPasscode = "";
    let newPasscode = "";
    let confirmPasscode = "";
    let error = "";
    let loading = false;

    // Reset state when dialog opens
    $: if (open) {
        step = 1;
        oldPasscode = "";
        newPasscode = "";
        confirmPasscode = "";
        error = "";
        loading = false;
    }

    function handleDigit(digit) {
        if (loading) return;
        error = "";

        if (step === 1) {
            if (oldPasscode.length < 6) oldPasscode += digit;
            if (oldPasscode.length === 6) verifyOldPasscode();
        } else if (step === 2) {
            if (newPasscode.length < 6) newPasscode += digit;
            if (newPasscode.length === 6) {
                step = 3;
            }
        } else if (step === 3) {
            if (confirmPasscode.length < 6) confirmPasscode += digit;
            if (confirmPasscode.length === 6) submitChange();
        }
    }

    function handleBackspace() {
        if (loading) return;
        error = "";

        if (step === 1) {
            oldPasscode = oldPasscode.slice(0, -1);
        } else if (step === 2) {
            newPasscode = newPasscode.slice(0, -1);
        } else if (step === 3) {
            confirmPasscode = confirmPasscode.slice(0, -1);
            if (confirmPasscode.length === 0) {
                step = 2; // Go back to step 2 if cleared
                newPasscode = ""; // Clear new passcode to re-enter
            }
        }
    }

    import { verifyPasscode } from "../../lib/api";

    async function verifyOldPasscode() {
        loading = true;
        try {
            const result = await verifyPasscode(oldPasscode);
            loading = false;

            if (result.valid) {
                step = 2;
            } else {
                if (result.error === "locked_out") {
                    error = result.message;
                } else if (result.error === "too_many_attempts") {
                    error = result.message;
                } else {
                    error = result.message || "Incorrect passcode";
                }
                oldPasscode = "";
            }
        } catch (e) {
            loading = false;
            error = e.message || "Verification failed";
            oldPasscode = "";
        }
    }

    async function submitChange() {
        if (newPasscode !== confirmPasscode) {
            error = "Passcodes do not match";
            confirmPasscode = "";
            step = 2; // Go back to re-enter new passcode
            newPasscode = "";
            return;
        }

        loading = true;
        const result = await passcode.change(oldPasscode, newPasscode);
        loading = false;

        if (result.success) {
            dispatch("success");
            open = false;
        } else {
            error = result.error || "Failed to change passcode";
            // Reset to step 1 on critical failure? Or just clear inputs?
            // Usually keep at step 3 or 1 depending on error.
            // If error is "Incorrect old passcode" (unlikely here since we verified), go to 1.
            if (result.error === "Incorrect old passcode") {
                step = 1;
                oldPasscode = "";
            } else {
                confirmPasscode = "";
            }
        }
    }

    function close() {
        open = false;
        dispatch("close");
    }
</script>

{#if open}
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
    >
        <div
            class="w-full max-w-md p-6 bg-card border border-border rounded-lg shadow-lg"
        >
            <!-- Header -->
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-xl font-semibold flex items-center gap-2">
                    <Lock size={20} class="text-primary" />
                    Change Passcode
                </h2>
                <button
                    on:click={close}
                    class="text-muted-foreground hover:text-foreground"
                >
                    <X size={20} />
                </button>
            </div>

            <!-- Steps Indicator -->
            <div class="flex items-center justify-center gap-2 mb-8">
                <div
                    class="h-2 w-2 rounded-full {step >= 1
                        ? 'bg-primary'
                        : 'bg-muted'}"
                ></div>
                <div
                    class="h-0.5 w-8 {step >= 2 ? 'bg-primary' : 'bg-muted'}"
                ></div>
                <div
                    class="h-2 w-2 rounded-full {step >= 2
                        ? 'bg-primary'
                        : 'bg-muted'}"
                ></div>
                <div
                    class="h-0.5 w-8 {step >= 3 ? 'bg-primary' : 'bg-muted'}"
                ></div>
                <div
                    class="h-2 w-2 rounded-full {step >= 3
                        ? 'bg-primary'
                        : 'bg-muted'}"
                ></div>
            </div>

            <!-- Title & Error -->
            <div class="text-center mb-6">
                <h3 class="text-lg font-medium mb-2">
                    {#if step === 1}
                        Enter Old Passcode
                    {:else if step === 2}
                        Enter New Passcode
                    {:else}
                        Confirm New Passcode
                    {/if}
                </h3>

                {#if error}
                    <p class="text-sm text-destructive animate-shake">
                        {error}
                    </p>
                {:else}
                    <p class="text-sm text-muted-foreground">
                        {#if step === 1}
                            Verify your current identity
                        {:else if step === 2}
                            Create a new 6-digit code
                        {:else}
                            Re-enter to confirm
                        {/if}
                    </p>
                {/if}
            </div>

            <!-- Dots Display -->
            <div class="flex justify-center gap-4 mb-8">
                {#each Array(6) as _, i}
                    <div
                        class="w-4 h-4 rounded-full border-2 transition-all duration-200
            {(step === 1
                            ? oldPasscode.length
                            : step === 2
                              ? newPasscode.length
                              : confirmPasscode.length) > i
                            ? 'bg-primary border-primary scale-110'
                            : 'border-muted-foreground/30'}"
                    ></div>
                {/each}
            </div>

            <!-- Keypad -->
            <div class="grid grid-cols-3 gap-4 max-w-[280px] mx-auto">
                {#each [1, 2, 3, 4, 5, 6, 7, 8, 9] as num}
                    <button
                        class="h-16 w-16 rounded-full text-2xl font-medium hover:bg-secondary transition-colors flex items-center justify-center"
                        on:click={() => handleDigit(num.toString())}
                        disabled={loading}
                    >
                        {num}
                    </button>
                {/each}
                <div class="h-16 w-16"></div>
                <button
                    class="h-16 w-16 rounded-full text-2xl font-medium hover:bg-secondary transition-colors flex items-center justify-center"
                    on:click={() => handleDigit("0")}
                    disabled={loading}
                >
                    0
                </button>
                <button
                    class="h-16 w-16 rounded-full hover:bg-destructive/10 hover:text-destructive transition-colors flex items-center justify-center"
                    on:click={handleBackspace}
                    disabled={loading}
                >
                    <ArrowRight class="rotate-180" size={24} />
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    @keyframes shake {
        0%,
        100% {
            transform: translateX(0);
        }
        25% {
            transform: translateX(-5px);
        }
        75% {
            transform: translateX(5px);
        }
    }
    .animate-shake {
        animation: shake 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
    }
</style>
