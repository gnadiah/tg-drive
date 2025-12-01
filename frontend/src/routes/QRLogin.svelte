<script>
    import { onMount, onDestroy, createEventDispatcher } from "svelte";
    import { requestQR, checkQRStatus } from "../lib/api";
    import { auth } from "../stores/auth";

    const dispatch = createEventDispatcher();
    import { Loader2, QrCode as QrIcon, RefreshCw } from "lucide-svelte";
    import QRCodeLib from "qrcode";

    let qrDataUrl = "";
    let tokenId = "";
    let status = "idle"; // idle, generating, waiting, scanned, confirmed, expired, error
    let error = "";
    let pollInterval = null;

    async function generateQR() {
        status = "generating";
        error = "";
        qrDataUrl = "";

        try {
            const res = await requestQR();
            tokenId = res.token_id;

            console.log("Generating QR code for URL:", res.qr_url);

            // Generate QR code as data URL (image)
            qrDataUrl = await QRCodeLib.toDataURL(res.qr_url, {
                width: 256,
                margin: 2,
                color: {
                    dark: "#000000",
                    light: "#FFFFFF",
                },
            });

            console.log("QR code data URL generated successfully");

            status = "waiting";
            startPolling();
        } catch (err) {
            console.error("QR generation error:", err);
            error = err.detail || err.message || "Failed to generate QR code";
            status = "error";
        }
    }

    function startPolling() {
        // Poll every 2 seconds
        pollInterval = setInterval(async () => {
            try {
                const res = await checkQRStatus(tokenId);
                console.log("QR Poll Result:", res);
                const newStatus = res.status;

                if (newStatus === "confirmed") {
                    console.log("QR Confirmed! Checking auth...");

                    if (res.needs_password) {
                        console.log("2FA required");
                        dispatch("needsPassword");
                        stopPolling();
                        return;
                    }

                    status = "confirmed";
                    stopPolling();
                    // Check auth and redirect
                    await auth.check();
                    console.log("Auth check complete");
                } else if (newStatus === "expired") {
                    console.log("QR Expired");
                    status = "expired";
                    stopPolling();
                } else if (newStatus === "error") {
                    console.error("QR Error:", res.error);
                    status = "error";
                    error = res.error || "QR login failed";
                    stopPolling();
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 2000);

        // Auto-expire after 35 seconds (30s server + 5s grace)
        setTimeout(() => {
            if (status === "waiting") {
                status = "expired";
                stopPolling();
            }
        }, 35000);
    }

    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    onMount(() => {
        generateQR();
    });

    onDestroy(() => {
        stopPolling();
    });
</script>

<div class="flex flex-col items-center justify-center space-y-6">
    {#if status === "generating"}
        <div class="flex flex-col items-center gap-4">
            <Loader2 class="animate-spin text-primary" size={48} />
            <p class="text-sm text-muted-foreground">Generating QR code...</p>
        </div>
    {:else if status === "waiting"}
        <div class="flex flex-col items-center gap-4 animate-in">
            <div
                class="p-4 bg-white dark:bg-white rounded-[var(--radius-lg)] shadow-lg"
            >
                <img src={qrDataUrl} alt="QR Code" class="w-64 h-64" />
            </div>
            <div class="text-center space-y-2">
                <p class="text-sm font-medium">Scan with Telegram app</p>
                <p class="text-xs text-muted-foreground">
                    Open Telegram → Settings → Devices → Scan QR
                </p>
            </div>
            <div class="flex items-center gap-2 text-xs text-muted-foreground">
                <div
                    class="w-2 h-2 bg-primary rounded-full animate-pulse"
                ></div>
                Waiting for confirmation...
            </div>
        </div>
    {:else if status === "confirmed"}
        <div class="flex flex-col items-center gap-4 animate-in">
            <div
                class="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center"
            >
                <QrIcon size={32} class="text-green-500" />
            </div>
            <p class="text-sm font-medium text-green-500">Login successful!</p>
        </div>
    {:else if status === "expired"}
        <div class="flex flex-col items-center gap-4 animate-in">
            <div
                class="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center"
            >
                <QrIcon size={32} class="text-muted-foreground" />
            </div>
            <div class="text-center space-y-2">
                <p class="text-sm font-medium text-muted-foreground">
                    QR code expired
                </p>
                <button
                    on:click={generateQR}
                    class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-[var(--radius-md)] text-sm font-medium hover:opacity-90 transition-all"
                >
                    <RefreshCw size={16} />
                    Generate new QR
                </button>
            </div>
        </div>
    {:else if status === "error"}
        <div class="flex flex-col items-center gap-4 animate-in">
            <div
                class="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center"
            >
                <QrIcon size={32} class="text-destructive" />
            </div>
            <div class="text-center space-y-2">
                <p class="text-sm font-medium text-destructive">{error}</p>
                <button
                    on:click={generateQR}
                    class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-[var(--radius-md)] text-sm font-medium hover:opacity-90 transition-all"
                >
                    <RefreshCw size={16} />
                    Try again
                </button>
            </div>
        </div>
    {/if}
</div>
