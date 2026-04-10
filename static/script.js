document.getElementById('preferencesForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const goals = document.getElementById('goals').value;
    const diet = document.getElementById('diet').value;
    const ingredients = document.getElementById('ingredients').value;

    const btnSubmit = document.getElementById('btn-submit');
    const spinner = document.getElementById('loadingSpinner');
    const btnText = btnSubmit.querySelector('span');

    // UI Loading state
    btnText.textContent = "Generating...";
    spinner.classList.remove('hidden');
    btnSubmit.disabled = true;

    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goals, diet, ingredients })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('recipeResult').innerHTML = data.recommendation;
            
            // Switch steps
            document.getElementById('step1').classList.remove('active');
            setTimeout(() => {
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'block';
                // Trigger reflow for animation
                void document.getElementById('step2').offsetWidth;
                document.getElementById('step2').classList.add('active');
            }, 500); // Wait for fade out
        } else {
            alert('Oh no! Could not generate recommendations: ' + data.error);
        }
    } catch (err) {
        alert('Failed to connect to the server. Make sure it is running!');
    } finally {
        // Reset UI
        btnText.textContent = "Generate Magic";
        spinner.classList.add('hidden');
        btnSubmit.disabled = false;
    }
});

document.getElementById('btn-back').addEventListener('click', () => {
    document.getElementById('step2').classList.remove('active');
    setTimeout(() => {
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step1').style.display = 'block';
        void document.getElementById('step1').offsetWidth;
        document.getElementById('step1').classList.add('active');
    }, 500);
});
