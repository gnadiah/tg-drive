<script>
    import { requestOtp, signIn } from "../lib/api";
    import { auth } from "../stores/auth";
    import {
        Cloud,
        Loader2,
        Phone,
        KeyRound,
        Lock,
        QrCode,
    } from "lucide-svelte";
    import { cn } from "../lib/utils";
    import QRLogin from "./QRLogin.svelte";

    let phone = "";
    let code = "";
    let password = "";
    let step = "phone"; // phone, code, password
    let error = "";
    let loading = false;
    let loginMethod = "phone"; // phone, qr

    async function handleRequestOtp(e) {
        e.preventDefault();
        loading = true;
        error = "";
        try {
            await requestOtp(phone);
            step = "code";
        } catch (err) {
            const detail = err.response?.data?.detail || "";
            if (
                detail.toLowerCase().includes("flood") ||
                detail.toLowerCase().includes("wait") ||
                detail.toLowerCase().includes("too many")
            ) {
                error =
                    "Too many code requests. Please wait 1-2 hours before trying again.";
            } else if (
                detail.toLowerCase().includes("phone") &&
                detail.toLowerCase().includes("invalid")
            ) {
                error =
                    "Invalid phone number format. Use international format: +1234567890";
            } else if (detail.toLowerCase().includes("banned")) {
                error = "This phone number is banned from Telegram.";
            } else {
                error =
                    detail ||
                    "Failed to send verification code. Please try again.";
            }
        } finally {
            loading = false;
        }
    }

    async function handleSignIn(e) {
        e.preventDefault();
        loading = true;
        error = "";
        try {
            const res = await signIn(phone, code, password);

            if (res.success) {
                await auth.check();
            } else if (res.status === "needs_password") {
                step = "password";
                error = "";
            } else if (res.error) {
                // Handle error returned as object
                const detail = res.error;
                if (
                    detail.toLowerCase().includes("phone") &&
                    detail.toLowerCase().includes("invalid")
                ) {
                    error = "Invalid phone number. Please check and try again.";
                } else if (
                    detail.toLowerCase().includes("code") &&
                    (detail.toLowerCase().includes("invalid") ||
                        detail.toLowerCase().includes("expired"))
                ) {
                    error =
                        "Invalid or expired verification code. Please request a new code.";
                    step = "phone";
                } else if (detail.toLowerCase().includes("password")) {
                    error = "Incorrect 2FA password. Please try again.";
                } else {
                    error =
                        detail || "Authentication failed. Please try again.";
                }
            }
        } catch (err) {
            console.error("Sign in error:", err);
            error = "An unexpected error occurred.";
        } finally {
            loading = false;
        }
    }
</script>

<div class="flex items-center justify-center min-h-screen bg-background">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div
            class="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl"
        ></div>
        <div
            class="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl"
        ></div>
    </div>

    <div
        class="w-full max-w-md p-8 m-4 glass rounded-[var(--radius-xl)] shadow-2xl animate-in z-10"
    >
        <div class="flex flex-col items-center mb-8 text-center">
            <div
                class="w-14 h-14 bg-gradient-to-br from-primary/20 to-primary/10 rounded-[var(--radius-lg)] flex items-center justify-center text-primary mb-4 shadow-sm"
            >
                <Cloud size={28} strokeWidth={2.5} />
            </div>
            <h1 class="text-2xl font-semibold tracking-tight">
                Sign in to TG Drive
            </h1>
            <p class="text-sm text-muted-foreground mt-2">
                Secure cloud storage powered by Telegram
            </p>
        </div>

        <!-- Tabs -->
        <div
            class="flex gap-2 p-1 bg-secondary/30 rounded-[var(--radius-md)] mb-6"
        >
            <button
                on:click={() => (loginMethod = "phone")}
                class={cn(
                    "flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-[var(--radius-sm)] text-sm font-medium transition-all",
                    loginMethod === "phone"
                        ? "bg-background shadow-sm text-foreground"
                        : "text-muted-foreground hover:text-foreground",
                )}
            >
                <Phone size={16} />
                Phone
            </button>
            <button
                on:click={() => (loginMethod = "qr")}
                class={cn(
                    "flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-[var(--radius-sm)] text-sm font-medium transition-all",
                    loginMethod === "qr"
                        ? "bg-background shadow-sm text-foreground"
                        : "text-muted-foreground hover:text-foreground",
                )}
            >
                <QrCode size={16} />
                QR Code
            </button>
        </div>

        {#if loginMethod === "phone"}
            {#if error}
                <div
                    class="bg-destructive/10 border border-destructive/20 text-destructive text-sm p-3.5 rounded-[var(--radius-md)] mb-6 animate-in"
                >
                    {error}
                </div>
            {/if}

            <form
                on:submit|preventDefault={step === "phone"
                    ? handleRequestOtp
                    : handleSignIn}
                class="space-y-5"
            >
                {#if step === "phone"}
                    <div class="space-y-2 animate-in">
                        <label for="phone" class="text-sm font-medium"
                            >Phone number</label
                        >
                        <div class="relative">
                            <Phone
                                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                                size={18}
                            />
                            <input
                                id="phone"
                                type="tel"
                                bind:value={phone}
                                placeholder="+1234567890"
                                class="flex h-11 w-full rounded-[var(--radius-md)] border border-input bg-background/50 pl-11 pr-4 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                required
                            />
                        </div>
                        <p class="text-xs text-muted-foreground">
                            Enter your phone number in international format
                        </p>
                    </div>
                {/if}

                {#if step === "code"}
                    <div class="space-y-2 animate-in">
                        <label for="code" class="text-sm font-medium"
                            >Verification code</label
                        >
                        <div class="relative">
                            <KeyRound
                                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                                size={18}
                            />
                            <input
                                id="code"
                                type="text"
                                bind:value={code}
                                placeholder="12345"
                                class="flex h-11 w-full rounded-[var(--radius-md)] border border-input bg-background/50 pl-11 pr-4 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                required
                            />
                        </div>
                        <p class="text-xs text-muted-foreground">
                            Enter the code sent to your Telegram app
                        </p>
                    </div>
                {/if}

                {#if step === "password"}
                    <div class="space-y-2 animate-in">
                        <label for="password" class="text-sm font-medium"
                            >2FA Password</label
                        >
                        <div class="relative">
                            <Lock
                                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                                size={18}
                            />
                            <input
                                id="password"
                                type="password"
                                bind:value={password}
                                placeholder="Enter your password"
                                class="flex h-11 w-full rounded-[var(--radius-md)] border border-input bg-background/50 pl-11 pr-4 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                required
                            />
                        </div>
                    </div>
                {/if}

                <button
                    type="submit"
                    disabled={loading}
                    class={cn(
                        "inline-flex items-center justify-center rounded-[var(--radius-md)] text-sm font-medium transition-all h-11 px-8 w-full shadow-sm",
                        "bg-primary text-primary-foreground hover:opacity-90",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        "disabled:opacity-50 disabled:pointer-events-none",
                    )}
                >
                    {#if loading}
                        <Loader2 class="mr-2 h-4 w-4 animate-spin" />
                        Please wait
                    {:else}
                        {step === "phone" ? "Continue" : "Sign in"}
                    {/if}
                </button>
            </form>
        {:else}
            <QRLogin
                on:needsPassword={() => {
                    loginMethod = "phone";
                    step = "password";
                    error = "";
                }}
            />
        {/if}
    </div>
</div>
