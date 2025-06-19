// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("Voting App Main JS Loaded");

    // Auto-dismiss flash messages after a few seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 500);
        }, 5000); // 5 seconds
    });

    // Dynamic option fields for poll creation
    const addOptionButton = document.getElementById('add-option-button');
    const optionsContainer = document.getElementById('poll-options-container');
    const pollForm = document.getElementById('create-poll-form');
    const optionsDataInput = document.getElementById('options_data');

    if (addOptionButton && optionsContainer && pollForm && optionsDataInput) {
        
        const createRemoveButton = () => {
            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.classList.add('btn', 'btn-danger', 'text-sm', 'p-2', 'flex-shrink-0');
            removeButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
            removeButton.title = 'Remove option';

            removeButton.addEventListener('click', function() {
                this.parentElement.remove();
                updateOptionPlaceholders();
            });
            return removeButton;
        };
        
        const updateOptionPlaceholders = () => {
            const currentInputs = optionsContainer.querySelectorAll('input[type="text"]');
            currentInputs.forEach((input, index) => {
                input.placeholder = 'Option ' + (index + 1);
            });
        };

        addOptionButton.addEventListener('click', function() {
            const optionIndex = optionsContainer.children.length + 1;
            const newOptionDiv = document.createElement('div');
            newOptionDiv.classList.add('flex', 'items-center', 'space-x-2', 'mb-2');
            
            const newOptionInput = document.createElement('input');
            newOptionInput.type = 'text';
            newOptionInput.name = 'dynamic_option_' + optionIndex;
            newOptionInput.classList.add('form-input', 'flex-grow');
            newOptionInput.placeholder = 'Option ' + optionIndex;
            
            const removeButton = createRemoveButton();

            newOptionDiv.appendChild(newOptionInput);
            newOptionDiv.appendChild(removeButton);
            optionsContainer.appendChild(newOptionDiv);
            newOptionInput.focus();
        });
        
        updateOptionPlaceholders();

        pollForm.addEventListener('submit', function(event) {
            const optionInputs = optionsContainer.querySelectorAll('input[type="text"]');
            const optionsTexts = [];
            optionInputs.forEach(input => {
                if (input.value.trim() !== '') {
                    optionsTexts.push(input.value.trim());
                }
            });
            optionsDataInput.value = JSON.stringify(optionsTexts);
        });
    }

    // Confirmation for delete buttons
    const deleteButtons = document.querySelectorAll('.confirm-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const message = button.getAttribute('data-confirm-message') || 'Are you sure you want to delete this item? This action cannot be undone.';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

});
