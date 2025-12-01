<script>
    import { createEventDispatcher } from "svelte";
    import { AlertTriangle, Trash2 } from "lucide-svelte";
    import Dialog from "./Dialog.svelte";

    export let open = false;

    const dispatch = createEventDispatcher();
    let confirmed = false;

    function handleConfirm() {
        if (confirmed) {
            dispatch("confirm");
            close();
        }
    }

    function close() {
        open = false;
        confirmed = false;
        dispatch("close");
    }
</script>

<Dialog bind:open on:close={close} maxWidth="max-w-md">
    <div class="space-y-6">
        <!-- Warning Icon -->
        <div
            class="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center"
        >
            <AlertTriangle class="w-8 h-8 text-destructive" />
        </div>

        <!-- Title -->
        <div class="text-center space-y-2">
            <h2 class="text-2xl font-semibold">Reset Everything?</h2>
            <p class="text-sm text-muted-foreground">
                This action cannot be undone
            </p>
        </div>

        <!-- Warning Content -->
        <div class="space-y-4 text-sm">
            <p class="text-muted-foreground">
                If you've forgotten your passcode, the only option is to reset
                all encrypted data and start fresh.
            </p>

            <div
                class="space-y-2 bg-destructive/10 p-4 rounded-lg border border-destructive/20"
            >
                <div
                    class="font-medium text-destructive flex items-center gap-2"
                >
                    <Trash2 class="w-4 h-4" />
                    Will be deleted:
                </div>
                <ul class="space-y-1 ml-6 text-destructive/90">
                    <li>• Passcode hash</li>
                    <li>• All encrypted file metadata (V2)</li>
                    <li>• File chunks remain on Telegram</li>
                </ul>
            </div>

            <div
                class="space-y-2 bg-primary/10 p-4 rounded-lg border border-primary/20"
            >
                <div class="font-medium text-primary">Will be kept:</div>
                <ul class="space-y-1 ml-6 text-primary/90">
                    <li>• Plaintext file metadata (V1)</li>
                    <li>• Your Telegram account</li>
                </ul>
            </div>
        </div>

        <!-- Confirmation Checkbox -->
        <label class="flex items-start gap-3 cursor-pointer">
            <input
                type="checkbox"
                bind:checked={confirmed}
                class="mt-1 w-4 h-4 rounded border-border"
            />
            <span class="text-sm text-muted-foreground">
                I understand that this will permanently delete all encrypted
                files and I cannot recover them.
            </span>
        </label>

        <!-- Actions -->
        <div class="flex gap-3">
            <button
                on:click={close}
                class="flex-1 px-4 py-2 border rounded-lg hover:bg-accent transition-colors"
            >
                Cancel
            </button>
            <button
                on:click={handleConfirm}
                disabled={!confirmed}
                class="flex-1 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
                Reset Everything
            </button>
        </div>
    </div>
</Dialog>
