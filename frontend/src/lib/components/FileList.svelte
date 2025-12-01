<script>
    import { onMount } from "svelte";
    import { fileStore } from "../../stores/files";
    import {
        File,
        Download,
        Edit2,
        Trash2,
        Grid,
        List,
        Upload,
        RefreshCw,
        Image,
        Video,
        Music,
        FileText,
        Loader2,
    } from "lucide-svelte";
    import { cn } from "../utils";
    import Dialog from "./Dialog.svelte";

    export let searchQuery = "";

    let viewMode = "grid"; // 'grid' or 'list'

    // Dialog state
    let renameDialog = { open: false, file: null, value: "" };
    let deleteDialog = { open: false, file: null };

    onMount(() => {
        fileStore.loadFiles();
    });

    function handleDownload(file) {
        fileStore.downloadFile(file);
    }

    function showRenameDialog(file) {
        renameDialog = { open: true, file, value: file.name };
    }

    async function confirmRename(event) {
        const newName = event.detail;
        if (!newName || newName === renameDialog.file.name) return;
        try {
            await fileStore.renameFile(renameDialog.file, newName);
        } catch (err) {
            console.error("Rename failed:", err);
        }
    }

    function showDeleteDialog(file) {
        deleteDialog = { open: true, file };
    }

    async function confirmDelete() {
        try {
            await fileStore.deleteFile(deleteDialog.file);
        } catch (err) {
            console.error("Delete failed:", err);
        }
    }

    function getFileIcon(filename) {
        const ext = filename.split(".").pop()?.toLowerCase();
        if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext))
            return {
                icon: Image,
                color: "text-purple-500",
                bg: "bg-purple-500/10",
            };
        if (["mp4", "mov", "avi", "mkv", "webm"].includes(ext))
            return { icon: Video, color: "text-red-500", bg: "bg-red-500/10" };
        if (["mp3", "wav", "ogg", "flac"].includes(ext))
            return {
                icon: Music,
                color: "text-yellow-500",
                bg: "bg-yellow-500/10",
            };
        if (["pdf", "doc", "docx", "txt", "md"].includes(ext))
            return {
                icon: FileText,
                color: "text-blue-500",
                bg: "bg-blue-500/10",
            };
        return {
            icon: File,
            color: "text-muted-foreground",
            bg: "bg-muted/50",
        };
    }

    function formatSize(bytes) {
        return (bytes / 1024 / 1024).toFixed(2) + " MB";
    }

    $: filteredFiles = $fileStore.files.filter((f) =>
        f.name.toLowerCase().includes(searchQuery.toLowerCase()),
    );
</script>

<!-- Dialogs -->
<Dialog
    bind:open={renameDialog.open}
    bind:value={renameDialog.value}
    type="prompt"
    title="Rename File"
    message="Enter a new name for this file:"
    confirmText="Rename"
    on:confirm={confirmRename}
/>

<Dialog
    bind:open={deleteDialog.open}
    type="confirm"
    title="Delete File"
    message={deleteDialog.file
        ? `Are you sure you want to delete "${deleteDialog.file.name}"? This action cannot be undone.`
        : ""}
    confirmText="Delete"
    destructive={true}
    on:confirm={confirmDelete}
/>

<div class="flex flex-col h-full">
    <!-- Toolbar -->
    <div class="flex items-center justify-between p-6 border-b border-border">
        <h2 class="text-lg font-semibold">My Files</h2>

        <div class="flex items-center gap-2">
            <div class="flex bg-secondary/50 p-0.5 rounded-[var(--radius-sm)]">
                <button
                    on:click={() => (viewMode = "grid")}
                    class={cn(
                        "p-2 rounded-[var(--radius-sm)] transition-colors",
                        viewMode === "grid"
                            ? "bg-background shadow-sm"
                            : "hover:bg-background/50",
                    )}
                    title="Grid view"
                >
                    <Grid
                        size={18}
                        class={viewMode === "grid"
                            ? "text-foreground"
                            : "text-muted-foreground"}
                    />
                </button>
                <button
                    on:click={() => (viewMode = "list")}
                    class={cn(
                        "p-2 rounded-[var(--radius-sm)] transition-colors",
                        viewMode === "list"
                            ? "bg-background shadow-sm"
                            : "hover:bg-background/50",
                    )}
                    title="List view"
                >
                    <List
                        size={18}
                        class={viewMode === "list"
                            ? "text-foreground"
                            : "text-muted-foreground"}
                    />
                </button>
            </div>

            <button
                on:click={() => fileStore.loadFiles()}
                class="p-2 rounded-[var(--radius-md)] hover:bg-secondary transition-colors"
                title="Refresh"
            >
                <RefreshCw
                    size={20}
                    class={cn(
                        "text-muted-foreground",
                        $fileStore.loading && "animate-spin",
                    )}
                />
            </button>

            <button
                on:click={() => fileStore.uploadFile()}
                class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-[var(--radius-md)] hover:opacity-90 transition-all shadow-sm"
            >
                <Upload size={18} />
                Upload
            </button>
        </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-auto p-6">
        {#if $fileStore.loading && $fileStore.files.length === 0}
            <div class="flex items-center justify-center h-64">
                <Loader2 size={32} class="animate-spin text-primary" />
            </div>
        {:else if filteredFiles.length === 0}
            <div
                class="flex flex-col items-center justify-center h-64 text-center"
            >
                <div
                    class="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mb-4"
                >
                    <Upload size={32} class="text-muted-foreground" />
                </div>
                <h3 class="text-lg font-medium mb-1">No files yet</h3>
                <p class="text-sm text-muted-foreground mb-4">
                    Upload files to get started
                </p>
                <button
                    on:click={() => fileStore.uploadFile()}
                    class="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground rounded-[var(--radius-md)] text-sm font-medium transition-colors"
                >
                    Select file
                </button>
            </div>
        {:else if viewMode === "grid"}
            <div
                class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4"
            >
                {#each filteredFiles as file (file.id)}
                    {@const fileIcon = getFileIcon(file.name)}
                    <div
                        class="group relative glass-border rounded-[var(--radius-lg)] p-4 hover:bg-secondary/30 transition-all cursor-pointer"
                    >
                        <div
                            class={cn(
                                "w-12 h-12 rounded-[var(--radius-md)] flex items-center justify-center mb-3 transition-transform group-hover:scale-110",
                                fileIcon.bg,
                            )}
                        >
                            <svelte:component
                                this={fileIcon.icon}
                                size={24}
                                class={fileIcon.color}
                            />
                        </div>
                        <h3
                            class="text-sm font-medium truncate mb-1"
                            title={file.name}
                        >
                            {file.name}
                        </h3>
                        <p class="text-xs text-muted-foreground">
                            {formatSize(file.size)}
                        </p>

                        <div
                            class="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <button
                                on:click|stopPropagation={() =>
                                    handleDownload(file)}
                                class="p-1.5 bg-background/80 rounded-[var(--radius-sm)] hover:bg-background shadow-sm"
                                title="Download"
                            >
                                <Download
                                    size={14}
                                    class="text-muted-foreground hover:text-foreground"
                                />
                            </button>
                            <button
                                on:click|stopPropagation={() =>
                                    showRenameDialog(file)}
                                class="p-1.5 bg-background/80 rounded-[var(--radius-sm)] hover:bg-background shadow-sm"
                                title="Rename"
                            >
                                <Edit2
                                    size={14}
                                    class="text-muted-foreground hover:text-foreground"
                                />
                            </button>
                            <button
                                on:click|stopPropagation={() =>
                                    showDeleteDialog(file)}
                                class="p-1.5 bg-background/80 rounded-[var(--radius-sm)] hover:bg-background shadow-sm"
                                title="Delete"
                            >
                                <Trash2 size={14} class="text-destructive" />
                            </button>
                        </div>
                    </div>
                {/each}
            </div>
        {:else}
            <div
                class="glass-border rounded-[var(--radius-lg)] overflow-hidden"
            >
                <table class="w-full">
                    <thead class="bg-secondary/30">
                        <tr
                            class="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider"
                        >
                            <th class="px-6 py-3">Name</th>
                            <th class="px-6 py-3">Size</th>
                            <th class="px-6 py-3">Type</th>
                            <th class="px-6 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-border">
                        {#each filteredFiles as file (file.id)}
                            {@const fileIcon = getFileIcon(file.name)}
                            <tr
                                class="group hover:bg-secondary/20 transition-colors"
                            >
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-3">
                                        <div
                                            class={cn(
                                                "p-2 rounded-[var(--radius-sm)]",
                                                fileIcon.bg,
                                            )}
                                        >
                                            <svelte:component
                                                this={fileIcon.icon}
                                                size={20}
                                                class={fileIcon.color}
                                            />
                                        </div>
                                        <span class="font-medium"
                                            >{file.name}</span
                                        >
                                    </div>
                                </td>
                                <td
                                    class="px-6 py-4 text-sm text-muted-foreground font-mono"
                                    >{formatSize(file.size)}</td
                                >
                                <td
                                    class="px-6 py-4 text-sm text-muted-foreground uppercase"
                                    >{file.name.split(".").pop()}</td
                                >
                                <td class="px-6 py-4">
                                    <div
                                        class="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <button
                                            on:click={() =>
                                                handleDownload(file)}
                                            class="p-2 hover:bg-secondary rounded-[var(--radius-sm)] transition-colors"
                                            title="Download"
                                        >
                                            <Download
                                                size={16}
                                                class="text-muted-foreground hover:text-foreground transition-colors"
                                            />
                                        </button>
                                        <button
                                            on:click={() =>
                                                showRenameDialog(file)}
                                            class="p-2 hover:bg-secondary rounded-[var(--radius-sm)] transition-colors"
                                            title="Rename"
                                        >
                                            <Edit2
                                                size={16}
                                                class="text-muted-foreground hover:text-foreground transition-colors"
                                            />
                                        </button>
                                        <button
                                            on:click={() =>
                                                showDeleteDialog(file)}
                                            class="p-2 hover:bg-secondary rounded-[var(--radius-sm)] transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2
                                                size={16}
                                                class="text-destructive"
                                            />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
    </div>
</div>
