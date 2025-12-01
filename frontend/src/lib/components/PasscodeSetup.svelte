<script>
    import { createEventDispatcher } from "svelte";
    import { Shield, ArrowRight, SkipForward } from "lucide-svelte";
    import PasscodeDialog from "./PasscodeDialog.svelte";

    const dispatch = createEventDispatcher();

    let step = "welcome"; // 'welcome' | 'set' | 'confirm'
    let firstPasscode = "";
    let error = null;

    function handleWelcomeContinue() {
        step = "set";
    }

    function handleSetPasscode(event) {
        firstPasscode = event.detail;
        step = "confirm";
        error = null;
    }

    function handleConfirmPasscode(event) {
        const confirmPasscode = event.detail;
        if (confirmPasscode === firstPasscode) {
            dispatch("complete", firstPasscode);
        } else {
            error = "Passcodes don't match. Please try again.";
            firstPasscode = "";
            step = "set";
        }
    }

    function handleSkip() {
        dispatch("skip");
    }
</script>

{#if step === "welcome"}
    <div
        class="flex flex-col items-center justify-center min-h-screen p-8 bg-background"
    >
        <div class="w-full max-w-md space-y-6 text-center">
            <div
                class="mx-auto w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-6"
            >
                <Shield class="w-12 h-12 text-primary" />
            </div>

            <h1 class="text-3xl font-semibold">Secure Your Files</h1>

            <p class="text-muted-foreground leading-relaxed">
                Set a 6-digit passcode to encrypt your file metadata. This adds
                an extra layer of security to your Telegram Drive.
            </p>

            <div
                class="space-y-3 text-sm text-left bg-card p-4 rounded-lg border"
            >
                <div class="flex gap-3">
                    <div class="text-primary">✓</div>
                    <div>Metadata is encrypted before uploading</div>
                </div>
                <div class="flex gap-3">
                    <div class="text-primary">✓</div>
                    <div>Only you can access your files</div>
                </div>
                <div class="flex gap-3">
                    <div class="text-destructive">⚠</div>
                    <div>Forgetting passcode = permanent data loss</div>
                </div>
            </div>

            <div class="space-y-3 pt-4">
                <button
                    on:click={handleWelcomeContinue}
                    class="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
                >
                    Set Passcode
                    <ArrowRight class="w-4 h-4" />
                </button>

                <button
                    on:click={handleSkip}
                    class="w-full flex items-center justify-center gap-2 px-6 py-3 border rounded-lg hover:bg-accent transition-colors text-sm text-muted-foreground"
                >
                    <SkipForward class="w-4 h-4" />
                    Skip (Not Recommended)
                </button>
            </div>
        </div>
    </div>
{:else if step === "set"}
    <PasscodeDialog title="Create Passcode" on:submit={handleSetPasscode} />
{:else if step === "confirm"}
    <PasscodeDialog
        title="Confirm Passcode"
        {error}
        on:submit={handleConfirmPasscode}
    />
{/if}
