// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("Voting App Main JS Loaded");

    // Mobile menu toggle (if you add a hamburger menu)
    // const menuButton = document.getElementById('mobile-menu-button');
    // const mobileMenu = document.getElementById('mobile-menu');
    // if (menuButton && mobileMenu) {
    //     menuButton.addEventListener('click', () => {
    //         mobileMenu.classList.toggle('hidden');
    //     });
    // }

    // Auto-dismiss flash messages after a few seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            // Add a class for fade-out animation
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            // Remove the element after animation
            setTimeout(() => message.remove(), 500);
        }, 5000); // 5 seconds
    });

    // Dynamic option fields for poll creation
    const addOptionButton = document.getElementById('add-option-button');
    const optionsContainer = document.getElementById('poll-options-container');
    const pollForm = document.getElementById('create-poll-form'); // Ensure your form has this ID
    const optionsDataInput = document.getElementById('options_data'); // Hidden input

    if (addOptionButton && optionsContainer && pollForm && optionsDataInput) {
        let optionCount = optionsContainer.getElementsByTagName('input').length;

        addOptionButton.addEventListener('click', function() {
            optionCount++;
            const newOptionDiv = document.createElement('div');
            newOptionDiv.classList.add('flex', 'items-center', 'space-x-2', 'mb-2');
            
            const newOptionInput = document.createElement('input');
            newOptionInput.type = 'text';
            newOptionInput.name = 'dynamic_option_' + optionCount; // Name not directly used by Flask if using JSON
            newOptionInput.classList.add('form-input', 'flex-grow');
            newOptionInput.placeholder = 'Option ' + (optionsContainer.children.length + 1);
            
            const removeButton = document.createElement('button');
            removeButton.type = 'button'; // Important: prevent form submission
            removeButton.classList.add('btn', 'btn-danger', 'text-sm', 'p-2');
            removeButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
            removeButton.title = 'Remove option';

            removeButton.addEventListener('click', function() {
                newOptionDiv.remove();
                // Re-number placeholders if needed, or just let them be
                updateOptionPlaceholders();
            });

            newOptionDiv.appendChild(newOptionInput);
            newOptionDiv.appendChild(removeButton);
            optionsContainer.appendChild(newOptionDiv);
            newOptionInput.focus();
        });

        // Function to update placeholders if options are removed
        function updateOptionPlaceholders() {
            const currentInputs = optionsContainer.querySelectorAll('input[type="text"]');
            currentInputs.forEach((input, index) => {
                input.placeholder = 'Option ' + (index + 1);
            });
        }
        
        // Initial setup for existing options (if any, though typically starts empty)
        updateOptionPlaceholders();


        // Before submitting the form, gather all option texts into the hidden field as JSON
        pollForm.addEventListener('submit', function(event) {
            const optionInputs = optionsContainer.querySelectorAll('input[type="text"]');
            const optionsTexts = [];
            optionInputs.forEach(input => {
                if (input.value.trim() !== '') {
                    optionsTexts.push(input.value.trim());
                }
            });
            
            if (optionsTexts.length < 2) {
                // Optionally show a client-side validation message
                // alert("Please provide at least two distinct options.");
                // The server-side validation will catch this too.
                // For better UX, you might want to prevent submission here and show an error.
                // For now, relying on server-side for robust validation.
            }
            
            optionsDataInput.value = JSON.stringify(optionsTexts);
            console.log("Submitting options:", optionsDataInput.value);
        });
    }

    // Confirmation for delete buttons (e.g., delete user in admin)
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
