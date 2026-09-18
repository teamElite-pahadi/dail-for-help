document.addEventListener("DOMContentLoaded", () => {
    const slugInput = document.querySelector('input[name="slug"]');
    const nameInput = document.querySelector('input[name="name"]');
    if (slugInput && nameInput && !slugInput.value) {
        nameInput.addEventListener("input", () => {
            slugInput.value = nameInput.value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
        });
    }
});
