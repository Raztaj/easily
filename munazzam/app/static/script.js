// انتظر حتى يتم تحميل محتوى الصفحة بالكامل قبل تشغيل الكود
document.addEventListener('DOMContentLoaded', function() {

    // ===========================================
    // ===== المنطق الخاص بالتنقل بين الشاشات =====
    // ===========================================
    const navLinks = document.querySelectorAll('.nav-link');
    const views = document.querySelectorAll('.view');

    // This logic is for a single-page application.
    // In a multi-page Flask app, the server will render the correct page,
    // so this client-side switching is not strictly necessary.
    // However, we can adapt it to set the 'active' class based on the current URL.

    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });


    // ========================================================
    // ===== التفاعلية الخاصة بصفحة إنشاء حملة جديدة =====
    // ========================================================
    const campaignPage = document.getElementById('new-campaign');
    if (campaignPage) {
        const campaignNameInput = document.getElementById('campaign-name');
        const summaryName = document.getElementById('summary-name');
        const tagsInput = document.getElementById('target-tags');
        const selectedTagsContainer = document.querySelector('.selected-tags');
        const summaryTagsContainer = document.getElementById('summary-tags');
        const summaryCount = document.getElementById('summary-count');

        let selectedTags = new Set();

        // Update campaign name in summary
        campaignNameInput.addEventListener('input', () => {
            summaryName.textContent = campaignNameInput.value.trim() || '--';
        });

        // Add tag on Enter
        tagsInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && tagsInput.value.trim() !== '') {
                e.preventDefault();
                const tagName = tagsInput.value.trim();
                selectedTags.add(tagName);
                tagsInput.value = '';
                renderTags();
                updateContactCount();
            }
        });

        function renderTags() {
            selectedTagsContainer.innerHTML = '';
            summaryTagsContainer.innerHTML = '';
            selectedTags.forEach(tag => {
                // Add to form view
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = tag;
                const removeBtn = document.createElement('button');
                removeBtn.innerHTML = '&times;';
                removeBtn.onclick = () => {
                    selectedTags.delete(tag);
                    renderTags();
                    updateContactCount();
                };
                tagEl.appendChild(removeBtn);
                selectedTagsContainer.appendChild(tagEl);

                // Add to summary view
                const summaryTagEl = document.createElement('span');
                summaryTagEl.className = 'tag';
                summaryTagEl.textContent = tag;
                summaryTagsContainer.appendChild(summaryTagEl);
            });
        }

        async function updateContactCount() {
            const tagsArray = Array.from(selectedTags);
            document.getElementById('hidden-tags').value = tagsArray.join(',');

            const antiSpamCheckbox = document.getElementById('anti-spam');
            const campaignName = campaignNameInput.value.trim();

            let requestBody = { tags: tagsArray };
            if (antiSpamCheckbox.checked && campaignName) {
                requestBody.exclude_campaign_name = campaignName;
            }

            try {
                const response = await fetch('/api/contacts/count', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody),
                });
                const data = await response.json();
                summaryCount.textContent = data.count;
            } catch (error) {
                console.error('Error fetching contact count:', error);
                summaryCount.textContent = 'Error';
            }
        }

        // Add event listeners to update count when shield is toggled or campaign name changes
        document.getElementById('anti-spam').addEventListener('change', updateContactCount);
        campaignNameInput.addEventListener('input', updateContactCount);

        // Initial count update
        updateContactCount();

        // --- Template Logic ---
        const saveTemplateBtn = document.getElementById('save-template-btn');
        const templateSelect = document.getElementById('template-select');
        const campaignMessageTextarea = document.getElementById('campaign-message');
        let templates = [];

        async function fetchTemplates() {
            try {
                const response = await fetch('/api/templates');
                templates = await response.json();

                templateSelect.innerHTML = '<option value="">اختر قالب...</option>';
                templates.forEach(t => {
                    const option = document.createElement('option');
                    option.value = t.id;
                    option.textContent = t.name;
                    templateSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error fetching templates:', error);
            }
        }

        templateSelect.addEventListener('change', () => {
            const selectedTemplate = templates.find(t => t.id == templateSelect.value);
            if (selectedTemplate) {
                campaignMessageTextarea.value = selectedTemplate.body;
            } else {
                campaignMessageTextarea.value = '';
            }
        });

        saveTemplateBtn.addEventListener('click', async () => {
            const messageBody = campaignMessageTextarea.value.trim();
            if (!messageBody) {
                alert('لا يمكن حفظ قالب فارغ.');
                return;
            }

            const templateName = prompt('الرجاء إدخال اسم للقالب:', '');
            if (templateName) {
                try {
                    const response = await fetch('/api/templates', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: templateName, body: messageBody }),
                    });
                    if (response.ok) {
                        alert('تم حفظ القالب بنجاح!');
                        fetchTemplates(); // Refresh the list
                    } else {
                        const errorData = await response.json();
                        alert(`خطأ: ${errorData.error}`);
                    }
                } catch (error) {
                    console.error('Error saving template:', error);
                    alert('حدث خطأ أثناء حفظ القالب.');
                }
            }
        });

        // Initial fetch of templates
        fetchTemplates();
    }
});
