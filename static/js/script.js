// Study RPG - Main JavaScript File

// Define global variables and functions first
let timer = null;
let questionStartTime = null;
let currentQuestionIndex = 0; // Ensure this is the single source of truth
let consecutiveCorrect = 0; // Primarily for training?
let totalXP = 0; // Global XP accumulation

// Global battle state (initialize defaults, can be overridden by initializeBattleMode)
window.bossHealth = 100;
window.playerHealth = 100;
window.battleScore = 0;


// Stop the timer
window.stopTimer = function() {
    if (timer) {
        clearTimeout(timer);
        timer = null;
        console.log("Timer stopped."); // Added log
    }
};

// Initialize global functions before DOM is ready
window.showQuestion = function(index) {
    console.log(`Attempting to show question at index: ${index}`); // Log index
    const questions = document.querySelectorAll('.question-item');
    if (!questions || questions.length === 0) {
        console.log('No questions found or questions list is empty.');
        // If no questions, maybe show results immediately?
        if (typeof window.showResults === 'function') {
             console.log("No questions found, calling showResults.");
             window.showResults();
        }
        return;
    }
    console.log(`Found ${questions.length} question elements.`); // Add log

    // Validate index
    if (isNaN(index) || index < 0) {
        console.error(`Invalid index received: ${index}. Cannot show question.`);
        // Optionally show results or stop if index is invalid after first question
        // if (index !== 0 && typeof window.showResults === 'function') {
        //     window.showResults();
        // }
        return;
    }

    if (index >= questions.length) {
        console.log(`Index ${index} is out of bounds (${questions.length} questions), showing results.`);
        if (typeof window.showResults === 'function') {
            window.showResults();
        }
        return;
    }

    // Hide all questions first
    questions.forEach((q, i) => {
         if (q && q.style) {
           q.style.display = 'none';
        } else {
           console.warn(`Element at index ${i} in questions NodeList is invalid or lacks style property.`);
        }
    });
    console.log(`Hid all question elements.`);

    // Show the current question
    const currentQuestionElement = questions[index];
    console.log(`Trying to access questions[${index}]. Element found:`, currentQuestionElement); // Log the element itself

    // Explicitly check if the element exists AND has a style property
    if (!currentQuestionElement || typeof currentQuestionElement.style === 'undefined') {
        console.error(`Element at index ${index} (questions[${index}]) is invalid or lacks style property. Cannot set display. Element:`, currentQuestionElement);
        // Show results if we can't display the question
        if (typeof window.showResults === 'function') {
             window.showResults();
        }
        return; // Stop execution if element is invalid
    }

    currentQuestionElement.style.display = 'block'; // Should be safe now
    currentQuestionIndex = index; // *** Update the global index ***
    console.log(`Set currentQuestionIndex to: ${currentQuestionIndex}`); // Log update

    // Reset form elements within the current question
    const form = currentQuestionElement.querySelector('form'); // Find the form inside the question
    if (form) {
        // Reset textarea if it exists (for training mode)
        const textarea = form.querySelector('textarea');
        if (textarea) {
            textarea.value = '';
            textarea.disabled = false;
        }

        // Reset radio buttons if they exist (for battle mode)
        const radios = form.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.checked = false;
            radio.disabled = false;
            // Reset visual feedback styles on options
            const labelContainer = radio.closest('.form-check');
            if (labelContainer) {
                labelContainer.classList.remove('correct-option', 'incorrect-option', 'selected-incorrect');
            }
        });

        // Re-enable submit button
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            // Optional: Reset button text if needed
        }

        // Reset feedback and XP display for the current question
        const feedbackElement = currentQuestionElement.querySelector(`[id^='answer-feedback']`); // More general selector
        const xpElement = currentQuestionElement.querySelector(`[id^='xp-earned']`);
        if (feedbackElement) {
            feedbackElement.style.display = 'none';
            feedbackElement.className = 'alert'; // Reset classes
            feedbackElement.innerHTML = ''; // Clear content
        }
        if (xpElement) {
            xpElement.style.visibility = 'hidden';
            xpElement.textContent = '+0 XP';
        }
    }

    // Start the timer for this question
    questionStartTime = Date.now();
    window.stopTimer(); // Ensure any previous timer is stopped before starting new one
    updateTimer(); // Start the timer loop

    // Update progress indicator if it exists
    const progressIndicator = document.getElementById('question-progress');
    if (progressIndicator) {
        progressIndicator.textContent = `Question ${index + 1} of ${questions.length}`;
    }
};

// Update the timer display
function updateTimer() {
    // No need to clear here, window.showQuestion handles clearing before starting
    // if (timer) clearTimeout(timer);

    const timerDisplay = document.getElementById('question-timer');
    if (!timerDisplay || !questionStartTime) return; // Exit if no display or start time

    const elapsedSeconds = Math.floor((Date.now() - questionStartTime) / 1000);
    timerDisplay.textContent = formatTime(elapsedSeconds);

    // Schedule next update
    timer = setTimeout(updateTimer, 1000);
}

// Format time as MM:SS
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Default show results function (can be overridden by initializeBattleMode)
window.showResults = function() {
    console.log("Default showResults called.");
    window.stopTimer();
    const questionContainer = document.getElementById('question-container');
    const resultsContainer = document.getElementById('results-container');

    if (questionContainer && resultsContainer) {
        questionContainer.style.display = 'none';
        resultsContainer.style.display = 'block';

        // Update total XP display
        const totalXpDisplay = document.getElementById('total-xp');
        if (totalXpDisplay) {
            totalXpDisplay.textContent = totalXP; // Use global totalXP
        }
    } else {
         console.warn("showResults: Could not find question or results container.");
    }
};

// Centralized feedback function
window.showFeedback = function(questionId, data) {
    console.log(`Global showFeedback called for QID ${questionId} with data:`, data);

    const questionElement = document.querySelector(`.question-item[data-question-id='${questionId}']`);
    if (!questionElement) {
        console.error(`Global showFeedback: Could not find question element for QID ${questionId}`);
        // Still schedule next step even if feedback display fails
        scheduleNextStepOrResults();
        return;
    }

    const feedbackElement = questionElement.querySelector(`[id^='answer-feedback']`);
    const xpElement = questionElement.querySelector(`[id^='xp-earned']`);
    const form = questionElement.querySelector('form');

    if (feedbackElement) {
        feedbackElement.style.display = 'block';
    } else {
        console.warn(`Global showFeedback: Could not find feedback element for QID ${questionId}`);
    }

    if (xpElement) {
        xpElement.style.visibility = 'visible';
        xpElement.textContent = `+${data.xp_earned} XP`;
        console.log(`Global showFeedback: Displayed XP: +${data.xp_earned}`);
    } else {
        console.warn(`Global showFeedback: Could not find XP element for QID ${questionId}`);
    }

    // Update global totalXP regardless of mode
    totalXP += data.xp_earned;
    console.log(`Global showFeedback: Total XP updated to ${totalXP}`);

    // Check if battle functions exist (meaning we are in battle mode)
    const isBattleMode = typeof window.damageBoss === 'function' && typeof window.damagePlayer === 'function';

    if (isBattleMode) {
        // --- Battle Mode Feedback Logic ---
        console.log("Global showFeedback: Applying BATTLE logic.");
        // Highlight options
        if (form && data.correct_answer !== undefined) {
            form.querySelectorAll('input[type="radio"]').forEach(radio => {
                const labelContainer = radio.closest('.form-check');
                if (!labelContainer) return;
                labelContainer.classList.remove('correct-option', 'incorrect-option', 'selected-incorrect');

                if (radio.value === data.correct_answer) {
                    labelContainer.classList.add('correct-option');
                } else if (radio.checked) {
                    labelContainer.classList.add('incorrect-option', 'selected-incorrect');
                } else {
                    labelContainer.classList.add('incorrect-option');
                }
            });
            console.log("Global showFeedback: Highlighted options");
        }

        // Display feedback text and apply damage/score
        if (data.is_correct) {
            if (feedbackElement) {
                feedbackElement.className = 'alert alert-success';
                feedbackElement.innerHTML = `<i class="fas fa-check-circle"></i> Correct! ${data.explanation || ''}`;
            }
            window.damageBoss(data.xp_earned); // Call global battle function
            console.log("Global showFeedback: Displayed correct feedback & damaged boss");
        } else {
            if (feedbackElement) {
                feedbackElement.className = 'alert alert-danger';
                feedbackElement.innerHTML = `<i class="fas fa-times-circle"></i> Incorrect. The correct answer was: <strong>${data.correct_answer || 'N/A'}</strong>. ${data.explanation || ''}`;
            }
            window.damagePlayer(10 + Math.floor(Math.random() * 10)); // Call global battle function
            console.log("Global showFeedback: Displayed incorrect feedback & damaged player");
        }

        // Update battle score (global)
        window.battleScore += data.xp_earned;
        const battleScoreElement = document.getElementById('battle-score');
        if (battleScoreElement) battleScoreElement.textContent = window.battleScore;
        console.log(`Global showFeedback: Battle score updated to ${window.battleScore}`);

        if (data.leveled_up) {
            console.log("Level Up detected!");
            // Add visual indicator if desired
        }
        // --- End Battle Mode Logic ---

    } else {
        // --- Non-Battle (Training) Mode Feedback Logic ---
        console.log("Global showFeedback: Applying TRAINING logic.");
        if (data.is_correct) {
            consecutiveCorrect++;
            if (feedbackElement) {
                 feedbackElement.className = 'alert alert-success';
                 feedbackElement.innerHTML = `<i class="fas fa-check-circle"></i> Correct! ${data.explanation}`;
            }
        } else {
            consecutiveCorrect = 0;
             if (feedbackElement) {
                feedbackElement.className = 'alert alert-danger';
                feedbackElement.innerHTML = `<i class="fas fa-times-circle"></i> Incorrect. ${data.explanation}`;
            }
        }
         if (xpElement) {
            // Optional: Add animation for training mode XP
            xpElement.classList.add('xp-gain');
            setTimeout(() => {
                xpElement.classList.remove('xp-gain');
            }, 1000);
        }
        // --- End Training Mode Logic ---
    }

    // Schedule next step (common to both modes)
    scheduleNextStepOrResults();
};


// Helper function to schedule next question or results
function scheduleNextStepOrResults() {
    const isBattleMode = typeof window.bossHealth !== 'undefined' && typeof window.playerHealth !== 'undefined';

    // Check battle win/loss conditions if in battle mode
    if (isBattleMode) {
         console.log(`scheduleNextStepOrResults: Checking battle status - Boss HP: ${window.bossHealth}, Player HP: ${window.playerHealth}`);
         if (window.bossHealth <= 0 || window.playerHealth <= 0) {
            console.log("scheduleNextStepOrResults: Battle ended. Scheduling results display.");
            window.stopTimer(); // Ensure timer is stopped
            // Use a slightly shorter delay for results display after battle ends
            setTimeout(window.showResults, 2000);
            return; // Don't schedule next question
        }
    }

    // Schedule next question after feedback display duration
    console.log("scheduleNextStepOrResults: Scheduling next question.");
    setTimeout(() => {
        // Use the global currentQuestionIndex directly
        console.log(`scheduleNextStepOrResults: Timeout triggered. Current index before increment: ${currentQuestionIndex}`); // Use global directly
        // Ensure index is treated as a number before incrementing
        const currentIndexNum = Number(currentQuestionIndex);
        if (isNaN(currentIndexNum)){
             console.error("scheduleNextStepOrResults: currentQuestionIndex is NaN before incrementing. Resetting to 0.");
             currentQuestionIndex = 0; // Reset to 0 if NaN somehow occurred
        }
        const nextIndex = currentQuestionIndex + 1; // Increment the global index
        console.log(`scheduleNextStepOrResults: Calculated next index: ${nextIndex}. Calling showQuestion.`);
        window.showQuestion(nextIndex); // Call global showQuestion
    }, 3000); // Show feedback for 3 seconds
}


// Submit answer function (primarily for training mode with textarea)
function submitAnswer() {
    window.stopTimer(); // Stop timer on submit

    const userAnswerInput = document.getElementById('user-answer'); // Assumes ID for training textarea
    if (!userAnswerInput) {
         console.error("submitAnswer (training): Could not find #user-answer input.");
         return;
    }

    console.log(`submitAnswer (training): Submitting answer for question index: ${currentQuestionIndex}`);

    const responseTime = (Date.now() - questionStartTime) / 1000;
    const userAnswer = userAnswerInput.value;

    const currentQuestion = document.querySelector('.question-item:not([style*="display: none"])');
    if (!currentQuestion) {
        console.error("submitAnswer (training): Could not find current question element.");
        return;
    }

    const questionId = currentQuestion.dataset.questionId;

    // Clear the answer field for the next question (training specific)
    userAnswerInput.value = '';

    // Show loading indicator (training specific)
    const submitButton = document.querySelector('#answer-form button[type="submit"]'); // Assumes ID for training form
    let originalButtonText = 'Submit Answer'; // Default
    if (submitButton) {
        originalButtonText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Evaluating...';
    }

    // Send the answer to the server for evaluation
    fetch('/answer', { // Use the correct endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add CSRF token if needed
        },
        body: JSON.stringify({
            question_id: questionId,
            answer: userAnswer,
            response_time: responseTime
        })
    })
    .then(response => response.json())
    .then(data => {
        // Process the response using the global feedback function
        window.showFeedback(questionId, data); // Pass questionId

        // Reset the button (training specific)
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
        // Note: showFeedback now handles scheduling the next question
    })
    .catch(error => {
        console.error('submitAnswer (training): Error submitting answer:', error);
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }

        // Display error message using global feedback function
        window.showFeedback(questionId, {
             is_correct: false,
             explanation: `Error: ${error.message}. Please try again.`,
             xp_earned: 0
        });
    });
}

// Default battle status handler (placeholder, might not be needed if showFeedback handles it)
// function handleBattleStatus(status) { ... }

// DOM ready function
document.addEventListener('DOMContentLoaded', function() {
    console.log('Study RPG - JavaScript initialized');

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize XP progress bars
    initializeXPProgressBars();

    // Initialize page-specific elements (like initializeBattleMode)
    // This needs to run BEFORE we try to show the first question
    initializePageSpecificElements();

    // Check if we are on a page with questions (training or battle)
    const questionContainer = document.getElementById('question-container');
    const firstQuestion = document.querySelector('.question-item');

    if (questionContainer && firstQuestion) {
         // Attach generic submit handler ONLY if NOT in battle mode
         const isBattleMode = document.getElementById('battle-arena'); // Check if battle arena exists
         if (!isBattleMode) {
             // Likely Training mode - attach the generic submitAnswer
             const answerForm = document.getElementById('answer-form'); // Assumes training uses ID="answer-form"
             if (answerForm) {
                 console.log("Attaching training submit handler to #answer-form");
                 answerForm.addEventListener('submit', function(e) {
                     e.preventDefault();
                     submitAnswer(); // The one that uses textarea
                 });
             } else {
                  console.warn("Training mode detected, but #answer-form not found.");
             }
         } else {
              console.log("Battle mode detected, submit handled by battle.html script.");
         }

        // Start with the first question (common for both modes)
        // Use setTimeout to ensure DOM is fully ready and page-specific init has run
        setTimeout(() => {
            console.log("DOMContentLoaded: Calling initial showQuestion(0)");
            window.showQuestion(0);
        }, 100); // Small delay
    } else {
         console.log("DOMContentLoaded: No questions found on this page.");
    }

});

// Initialize page-specific elements based on current page
function initializePageSpecificElements() {
    // Battle page specific
    const battleArena = document.getElementById('battle-arena');
    if (battleArena) {
        initializeBattleMode();
    }

    // Profile page specific
    const performanceChart = document.getElementById('performance-chart');
    if (performanceChart) {
        initializeProfileCharts();
    }

    // Training page specific (might not need specific init anymore)
    // const trainingProgress = document.getElementById('training-progress');
    // if (trainingProgress) {
    //     initializeTrainingMode();
    // }
}

// Add function to initialize XP progress bars
function initializeXPProgressBars() {
    const progressBars = document.querySelectorAll('.xp-progress-bar');
    progressBars.forEach(bar => {
        const xp = parseInt(bar.dataset.xp, 10) || 0;
        const progress = xp % 100;
        bar.style.width = progress + '%';
        bar.setAttribute('aria-valuenow', progress);
    });
}

// Training mode initialization (placeholder if needed)
// function initializeTrainingMode() { ... }

// Battle mode initialization
function initializeBattleMode() {
    console.log('Battle mode initialized');

    // Attach battle functions to window scope so global showFeedback can call them
    // Ensure these functions are defined within this scope or globally accessible
    window.damageBoss = damageBoss;
    window.damagePlayer = damagePlayer;
    window.showBattleEffect = showBattleEffect;
    window.updateBattleMessage = updateBattleMessage;

    // Initialize global battle state variables from DOM/defaults
    const scoreElement = document.getElementById('battle-score');
    const initialScore = scoreElement ? parseInt(scoreElement.textContent, 10) : 0;
    const bossHealthElement = document.getElementById('boss-health-bar');
    const initialBossHealth = bossHealthElement ? parseInt(bossHealthElement.getAttribute('aria-valuenow'), 10) : 100;
    const playerHealthElement = document.getElementById('player-health-bar');
    const initialPlayerHealth = playerHealthElement ? parseInt(playerHealthElement.getAttribute('aria-valuenow'), 10) : 100;

    window.bossHealth = initialBossHealth;
    window.playerHealth = initialPlayerHealth;
    window.battleScore = initialScore;
    // Reset global totalXP per battle? Or accumulate across sessions? Assuming accumulate for now.
    // window.totalXP = 0; // Uncomment to reset XP per battle

    console.log(`Initial Battle State: BossHP=${window.bossHealth}, PlayerHP=${window.playerHealth}, Score=${window.battleScore}`);


    // Override the results function for battle mode
    window.showResults = function() {
        console.log("Battle showResults override called.");
        window.stopTimer(); // Ensure timer is stopped
        const questionContainer = document.getElementById('question-container');
        const resultsContainer = document.getElementById('results-container');
        const battleArena = document.getElementById('battle-arena');

        if (questionContainer) questionContainer.style.display = 'none';
        if (battleArena) battleArena.style.display = 'none'; // Hide arena too

        if (resultsContainer) {
            resultsContainer.style.display = 'block';

            // Update total XP and score displays using global state
            const totalXpDisplay = document.getElementById('total-xp');
            if (totalXpDisplay) {
                totalXpDisplay.textContent = window.totalXP || 0; // Use global totalXP
            }

            const finalScoreDisplay = document.getElementById('final-score');
            if (finalScoreDisplay) {
                finalScoreDisplay.textContent = window.battleScore || 0; // Use global battleScore
            }

            // Show victory or defeat based on global boss health
            const victoryContainer = document.getElementById('victory-container');
            const defeatContainer = document.getElementById('defeat-container');

            if (victoryContainer && defeatContainer) {
                if (window.bossHealth <= 0) {
                    console.log("Battle Result: VICTORY");
                    victoryContainer.style.display = 'block';
                    defeatContainer.style.display = 'none';
                } else {
                     console.log("Battle Result: DEFEAT");
                    victoryContainer.style.display = 'none';
                    defeatContainer.style.display = 'block';
                }
            } else {
                 console.warn("Battle results: Missing victory or defeat container.");
            }
        } else {
             console.error("Battle results: Missing results container.");
        }
    };
}

// --- Battle Mechanics Functions (Should be available in battle mode) ---
// These need to be defined so initializeBattleMode can attach them to window

function damageBoss(amount) {
    console.log(`damageBoss called with amount: ${amount}`);
    const healthBar = document.getElementById('boss-health-bar');
    const bossIcon = document.querySelector('.boss-icon');
    const healthLabel = document.querySelector('.health-label'); // Target the specific label

    if (!healthBar || !bossIcon || !healthLabel) {
         console.error("damageBoss: Missing healthBar, bossIcon, or healthLabel element");
         return;
    }

    // Use global showBattleEffect if available
    if(typeof window.showBattleEffect === 'function') window.showBattleEffect(amount, 'damage', '.boss-container');

    bossIcon.classList.add('damaged');
    setTimeout(() => { bossIcon.classList.remove('damaged'); }, 500);

    window.bossHealth = Math.max(0, window.bossHealth - amount); // Update global state
    const healthPercent = (window.bossHealth / 100) * 100;
    healthBar.style.width = `${healthPercent}%`;
    healthBar.setAttribute('aria-valuenow', window.bossHealth);
    healthLabel.textContent = `Boss HP: ${window.bossHealth}/100`; // Update label text

    // Use global updateBattleMessage if available
    if(typeof window.updateBattleMessage === 'function') window.updateBattleMessage(true, amount);

    if (window.bossHealth <= 0) {
        // Feedback handled by showFeedback/showResults now
        console.log("Boss health reached 0.");
    }
    console.log(`damageBoss finished. New bossHealth: ${window.bossHealth}`);
}

function damagePlayer(amount) {
    console.log(`damagePlayer called with amount: ${amount}`);
    const healthBar = document.getElementById('player-health-bar');

    if (!healthBar) {
        console.error("damagePlayer: Missing player-health-bar element");
        return;
    }

    // Use global showBattleEffect if available
    if(typeof window.showBattleEffect === 'function') window.showBattleEffect(amount, 'damage', '.player-health-bar');

    window.playerHealth = Math.max(0, window.playerHealth - amount); // Update global state
    const healthPercent = (window.playerHealth / 100) * 100;
    healthBar.style.width = `${healthPercent}%`;
    healthBar.setAttribute('aria-valuenow', window.playerHealth);

    // Use global updateBattleMessage if available
    if(typeof window.updateBattleMessage === 'function') window.updateBattleMessage(false, amount);

    if (window.playerHealth <= 0) {
         // Feedback handled by showFeedback/showResults now
         console.log("Player health reached 0.");
    }
    console.log(`damagePlayer finished. New playerHealth: ${window.playerHealth}`);
}

function showBattleEffect(amount, type, targetSelector) {
    // This function seems okay, ensure it's defined globally or within scope
    console.log(`showBattleEffect called: amount=${amount}, type=${type}, target=${targetSelector}`);
    const target = document.querySelector(targetSelector);
    const arena = document.getElementById('battle-arena'); // Effects should be relative to arena
    if (!target || !arena) {
        console.error(`showBattleEffect: Target (${targetSelector}) or Arena not found.`);
        return;
    }
    const effect = document.createElement('div');
    effect.className = `battle-effect ${type}`;
    effect.textContent = type === 'damage' ? `-${amount}` : `+${amount}`;

    // Position relative to the arena, near the target
    const rect = target.getBoundingClientRect();
    const arenaRect = arena.getBoundingClientRect();
    effect.style.position = 'absolute';
    effect.style.left = `${rect.left - arenaRect.left + (rect.width / 2) - 15}px`; // Approx center
    effect.style.top = `${rect.top - arenaRect.top - 30}px`; // Above target

    arena.appendChild(effect); // Append to arena

    setTimeout(() => { effect.remove(); }, 1500);
    console.log("showBattleEffect finished.");
}

function updateBattleMessage(playerAttacking, amount) {
    // This function seems okay, ensure it's defined globally or within scope
    console.log(`updateBattleMessage called: playerAttacking=${playerAttacking}, amount=${amount}`);
    const messageElement = document.getElementById('battle-message');
    if (!messageElement) {
        console.error("updateBattleMessage: Missing battle-message element");
        return;
    }
    if (playerAttacking) {
        messageElement.innerHTML = `<p class="mb-0">You attacked the boss for <span class="text-danger">${amount}</span> damage!</p>`;
    } else {
        messageElement.innerHTML = `<p class="mb-0">The boss attacked you for <span class="text-danger">${amount}</span> damage!</p>`;
    }
    console.log("updateBattleMessage finished.");
}

// --- End Battle Mechanics Functions ---


// Initialize charts on the profile page (remains the same)
function initializeProfileCharts() {
    // This requires Chart.js to be loaded
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not available - skipping chart initialization');
        return;
    }
    
    const chartContainer = document.getElementById('performance-chart');
    if (!chartContainer) return;
    
    const ctx = chartContainer.getContext('2d');
    
    // Sample data - replace with actual data from the server
    const performanceData = {
        labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        datasets: [{
            label: 'Questions Answered',
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1,
            data: [12, 8, 15, 5, 7, 9, 3]
        }, {
            label: 'XP Earned',
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
            borderColor: 'rgb(75, 192, 192)',
            borderWidth: 1,
            data: [65, 40, 80, 25, 35, 45, 15]
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: performanceData,
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            responsive: true
        }
    });
}