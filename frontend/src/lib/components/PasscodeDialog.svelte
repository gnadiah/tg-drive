<script>
    import { createEventDispatcher } from "svelte";
    import { Lock, Delete } from "lucide-svelte";

    export let title = "Enter Passcode";
    export let error = null;
    export let attemptsRemaining = 5;
    export let lockedUntil = null;
    export let loading = false;

    const dispatch = createEventDispatcher();

    let passcode = "";
    let lockCountdown = 0;
    let countdownInterval;

    // Update countdown if locked
    $: if (lockedUntil) {
        updateCountdown();
    } else {
        clearInterval(countdownInterval);
        lockCountdown = 0;
    }

    function updateCountdown() {
        if (!lockedUntil) return;

        lockCountdown = Math.max(
            0,
            Math.ceil((lockedUntil - Date.now()) / 1000),
        );

        if (lockCountdown > 0) {
            clearInterval(countdownInterval);
            countdownInterval = setInterval(() => {
                lockCountdown = Math.max(
                    0,
                    Math.ceil((lockedUntil - Date.now()) / 1000),
                );
                if (lockCountdown === 0) {
                    clearInterval(countdownInterval);
                    dispatch("unlocked");
                }
            }, 1000);
        }
    }

    function handleDigit(digit) {
        if (loading || lockedUntil) return;
        if (passcode.length < 6) {
            passcode += digit;
            if (passcode.length === 6) {
                submit();
            }
        }
    }

    function handleBackspace() {
        if (loading || lockedUntil) return;
        passcode = passcode.slice(0, -1);
    }

    function submit() {
        if (passcode.length === 6 && !loading) {
            dispatch("submit", passcode);
            passcode = ""; // Clear for next attempt
        }
    }

    function handleForgot() {
        dispatch("forgot");
    }

    const digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0"];
</script>

<div
    class="flex flex-col items-center justify-center min-h-screen p-8 bg-background"
>
    <div class="w-full max-w-md space-y-8">
        <!-- Header -->
        <div class="text-center space-y-2">
            <div
                class="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4"
            >
                <Lock class="w-8 h-8 text-primary" />
            </div>
            <h1 class="text-2xl font-semibold">{title}</h1>
            {#if lockedUntil && lockCountdown > 0}
                <p class="text-sm text-destructive font-medium">
                    Locked for {lockCountdown}s
                </p>
            {:else if error}
                <p class="text-sm text-destructive">{error}</p>
            {:else if attemptsRemaining < 5}
                <p class="text-sm text-muted-foreground">
                    {attemptsRemaining} attempts remaining
                </p>
            {/if}
        </div>

        <!-- Passcode Dots -->
        <div class="flex justify-center gap-3">
            {#each Array(6) as _, i}
                <div
                    class="w-4 h-4 rounded-full border-2 transition-all duration-200"
                    class:bg-primary={i < passcode.length}
                    class:border-primary={i < passcode.length}
                    class:border-border={i >= passcode.length}
                ></div>
            {/each}
        </div>

        <!-- Numeric Keypad -->
        <div class="grid grid-cols-3 gap-4">
            {#each digits as digit}
                {#if digit}
                    <button
                        on:click={() => handleDigit(digit)}
                        disabled={loading || !!lockedUntil}
                        class="aspect-square rounded-lg border bg-card hover:bg-accent transition-colors text-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {digit}
                    </button>
                {:else}
                    <div></div>
                {/if}
            {/each}

            <!-- Backspace Button -->
            <button
                on:click={handleBackspace}
                disabled={loading || !!lockedUntil || passcode.length === 0}
                class="aspect-square rounded-lg border bg-card hover:bg-accent transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <Delete class="w-6 h-6" />
            </button>
        </div>

        <!-- Forgot Passcode Link -->
        <div class="text-center">
            <button
                on:click={handleForgot}
                disabled={loading}
                class="text-sm text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
            >
                Forgot passcode?
            </button>
        </div>
    </div>
</div>

<style>
    .aspect-square {
        aspect-ratio: 1;
    }
</style>
