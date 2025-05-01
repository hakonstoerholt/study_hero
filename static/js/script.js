// Study RPG - Main JavaScript File

// Define global variables and functions first
let timer = null;
let questionStartTime = null;
let currentQuestionIndex = 0;
let consecutiveCorrect = 0;
let totalXP = 0;

// Initialize global functions before DOM is ready
window.showQuestion = function(index) {
    const questions = document.querySelectorAll('.question-item');
    if (!questions || questions.length === 0) return;
    
    if (index >= questions.length) {
        // No more questions, show results
        if (typeof window.showResults === 'function') {
            window.showResults();
        }
        return;
    }

    // Hide all questions first
    questions.forEach(q => q.style.display = 'none');

    // Show the current question
    questions[index].style.display = 'block';
    currentQuestionIndex = index;

    // Start the timer for this question
    questionStartTime = Date.now();
    updateTimer();

    // Update progress indicator if it exists
    const progressIndicator = document.getElementById('question-progress');
    if (progressIndicator) {
        progressIndicator.textContent = `Question ${index + 1} of ${questions.length}`;
    }
};

// Update the timer display
function updateTimer() {
    if (timer) clearTimeout(timer);
    
    const timerDisplay = document.getElementById('question-timer');
    if (!timerDisplay) return;
    
    const elapsedSeconds = Math.floor((Date.now() - questionStartTime) / 1000);
    timerDisplay.textContent = formatTime(elapsedSeconds);
    
    // Update every second
    timer = setTimeout(updateTimer, 1000);
}

// Format time as MM:SS
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Default show results function that can be overridden by specific pages
window.showResults = function() {
    const questionContainer = document.getElementById('question-container');
    const resultsContainer = document.getElementById('results-container');
    
    if (questionContainer && resultsContainer) {
        questionContainer.style.display = 'none';
        resultsContainer.style.display = 'block';
        
        // Update total XP display
        const totalXpDisplay = document.getElementById('total-xp');
        if (totalXpDisplay) {
            totalXpDisplay.textContent = totalXP;
        }
    }
};

// Default feedback function that can be overridden by specific pages
window.showFeedback = function(data, responseTime) {
    const feedbackElement = document.getElementById('answer-feedback');
    const xpElement = document.getElementById('xp-earned');
    
    if (!feedbackElement || !xpElement) return;
    
    // Update consecutive correct count
    if (data.is_correct) {
        consecutiveCorrect++;
        feedbackElement.className = 'alert alert-success';
        feedbackElement.innerHTML = `<i class="fas fa-check-circle"></i> Correct! ${data.explanation}`;
    } else {
        consecutiveCorrect = 0;
        feedbackElement.className = 'alert alert-danger';
        feedbackElement.innerHTML = `<i class="fas fa-times-circle"></i> Incorrect. ${data.explanation}`;
    }
    
    // Show XP earned
    totalXP += data.xp_earned;
    xpElement.textContent = `+${data.xp_earned} XP`;
    xpElement.classList.add('xp-gain');
    
    // Handle battle status update if applicable
    if (data.battle_status && data.battle_status !== 'in-progress') {
        if (typeof handleBattleStatus === 'function') {
            handleBattleStatus(data.battle_status);
        }
    }
    
    // Remove animation class after animation completes
    setTimeout(() => {
        xpElement.classList.remove('xp-gain');
    }, 1000);
};

// Submit answer function
function submitAnswer() {
    // Stop the timer
    if (timer) clearTimeout(timer);
    
    const userAnswerInput = document.getElementById('user-answer');
    if (!userAnswerInput) return;
    
    const responseTime = (Date.now() - questionStartTime) / 1000;
    const userAnswer = userAnswerInput.value;
    
    const currentQuestion = document.querySelector('.question-item:not([style*="display: none"])');
    if (!currentQuestion) return;
    
    const questionId = currentQuestion.dataset.questionId;
    
    // Clear the answer field for the next question
    userAnswerInput.value = '';
    
    // Show loading indicator
    const submitButton = document.querySelector('#answer-form button[type="submit"]');
    if (!submitButton) return;
    
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Evaluating...';
    
    // Send the answer to the server for evaluation
    fetch('/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question_id: questionId,
            answer: userAnswer,
            response_time: responseTime
        })
    })
    .then(response => response.json())
    .then(data => {
        // Process the response
        window.showFeedback(data, responseTime);
        
        // Reset the button
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
        
        // After a delay, show the next question or results
        setTimeout(() => {
            const nextIndex = currentQuestionIndex + 1;
            window.showQuestion(nextIndex);
        }, 3000); // Show feedback for 3 seconds
    })
    .catch(error => {
        console.error('Error submitting answer:', error);
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
        
        // Display error message
        const feedbackElement = document.getElementById('answer-feedback');
        if (feedbackElement) {
            feedbackElement.className = 'alert alert-danger';
            feedbackElement.innerHTML = '<i class="fas fa-exclamation-circle"></i> An error occurred while submitting your answer. Please try again.';
        }
    });
}

// Default battle status handler that can be overridden
function handleBattleStatus(status) {
    const battleStatusElement = document.getElementById('battle-status');
    if (!battleStatusElement) return;
    
    if (status === 'won') {
        battleStatusElement.innerHTML = '<div class="alert alert-success"><i class="fas fa-trophy"></i> You won the battle!</div>';
    } else if (status === 'lost') {
        battleStatusElement.innerHTML = '<div class="alert alert-danger"><i class="fas fa-skull-crossbones"></i> You lost the battle!</div>';
    }
}

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

    // Initialize question handling
    const answerForm = document.getElementById('answer-form');
    if (answerForm) {
        answerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitAnswer();
        });

        // Start with the first question if we're in question mode
        const questionContainer = document.getElementById('question-container');
        if (questionContainer) {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                window.showQuestion(0);
            }, 100);
        }
    }

    // Initialize page-specific elements
    initializePageSpecificElements();
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
    
    // Training page specific
    const trainingProgress = document.getElementById('training-progress');
    if (trainingProgress) {
        initializeTrainingMode();
    }
}

// Add function to initialize XP progress bars
function initializeXPProgressBars() {
    const progressBars = document.querySelectorAll('.xp-progress-bar');
    progressBars.forEach(bar => {
        const xp = parseInt(bar.dataset.xp, 10) || 0;
        const progress = xp % 100;
        bar.style.width = progress + '%';
        bar.setAttribute('aria-valuenow', progress);
        // Optional: Update text content if needed, though templates handle it
        // bar.textContent = `XP: ${progress}/100`; 
    });
}

// Training mode initialization
function initializeTrainingMode() {
    console.log('Training mode initialized');
    
    // Make feedback visible when needed
    const feedbackElement = document.getElementById('answer-feedback');
    if (feedbackElement) {
        feedbackElement.style.display = 'block';
    }
}

// Battle mode initialization
function initializeBattleMode() {
    console.log('Battle mode initialized');
    
    // Override the feedback function for battle mode
    window.showFeedback = function(data, responseTime) {
        const feedbackElement = document.getElementById('answer-feedback');
        const xpElement = document.getElementById('xp-earned');
        
        if (!feedbackElement || !xpElement) return;
        
        // Standard feedback display
        if (data.is_correct) {
            consecutiveCorrect++;
            feedbackElement.className = 'alert alert-success';
            feedbackElement.innerHTML = `<i class="fas fa-check-circle"></i> Correct! ${data.explanation}`;
            
            // Damage the boss
            const damage = data.xp_earned;
            damageBoss(damage);
        } else {
            consecutiveCorrect = 0;
            feedbackElement.className = 'alert alert-danger';
            feedbackElement.innerHTML = `<i class="fas fa-times-circle"></i> Incorrect. ${data.explanation}`;
            
            // Player takes damage
            const damage = 10 + Math.floor(Math.random() * 10);
            damagePlayer(damage);
        }
        
        // Update battle score
        if (typeof battleScore !== 'undefined') {
            battleScore += data.xp_earned;
            const battleScoreElement = document.getElementById('battle-score');
            if (battleScoreElement) {
                battleScoreElement.textContent = battleScore;
            }
        }
        
        // Show XP earned
        totalXP += data.xp_earned;
        xpElement.textContent = `+${data.xp_earned} XP`;
        xpElement.classList.add('xp-gain');
        
        // Handle battle status update
        if (data.battle_status && data.battle_status !== 'in-progress') {
            handleBattleStatus(data.battle_status);
        }
        
        // Remove animation class after animation completes
        setTimeout(() => {
            xpElement.classList.remove('xp-gain');
        }, 1000);
    };
    
    // Override the results function for battle mode
    window.showResults = function() {
        const questionContainer = document.getElementById('question-container');
        const resultsContainer = document.getElementById('results-container');
        const battleArena = document.getElementById('battle-arena');
        
        if (questionContainer && resultsContainer) {
            questionContainer.style.display = 'none';
            if (battleArena) battleArena.style.display = 'none';
            resultsContainer.style.display = 'block';
            
            // Update total XP and score displays
            const totalXpDisplay = document.getElementById('total-xp');
            if (totalXpDisplay) {
                totalXpDisplay.textContent = totalXP;
            }
            
            const finalScoreDisplay = document.getElementById('final-score');
            if (finalScoreDisplay && typeof battleScore !== 'undefined') {
                finalScoreDisplay.textContent = battleScore;
            }
            
            // Show victory or defeat based on boss health
            if (typeof bossHealth !== 'undefined') {
                const victoryContainer = document.getElementById('victory-container');
                const defeatContainer = document.getElementById('defeat-container');
                
                if (bossHealth <= 0 && victoryContainer) {
                    victoryContainer.style.display = 'block';
                } else if (defeatContainer) {
                    defeatContainer.style.display = 'block';
                }
            }
        }
    };
    
    // Make feedback visible when needed
    const feedbackElement = document.getElementById('answer-feedback');
    if (feedbackElement) {
        feedbackElement.style.display = 'block';
    }
}

// Battle mode functions
// These are conditionally used only when in battle mode
function damageBoss(amount) {
    if (typeof bossHealth === 'undefined') {
        window.bossHealth = 100;
    }
    
    const healthBar = document.getElementById('boss-health-bar');
    const bossIcon = document.querySelector('.boss-icon');
    
    if (!healthBar || !bossIcon) return;
    
    // Create damage effect
    showBattleEffect(amount, 'damage', '.boss-container');
    
    // Animate boss
    bossIcon.classList.add('damaged');
    setTimeout(() => {
        bossIcon.classList.remove('damaged');
    }, 500);
    
    // Update health
    window.bossHealth = Math.max(0, window.bossHealth - amount);
    const healthPercent = (window.bossHealth / 100) * 100;
    healthBar.style.width = `${healthPercent}%`;
    healthBar.setAttribute('aria-valuenow', window.bossHealth);
    
    const healthLabel = document.querySelector('.health-label');
    if (healthLabel) {
        healthLabel.textContent = `Boss HP: ${window.bossHealth}/100`;
    }
    
    // Update battle message
    updateBattleMessage(true, amount);
    
    // Check if boss is defeated
    if (window.bossHealth <= 0) {
        if (healthBar) healthBar.style.width = '0%';
        
        const battleMessage = document.getElementById('battle-message');
        if (battleMessage) {
            battleMessage.innerHTML = '<p class="text-success mb-0">Boss defeated! Victory is yours!</p>';
        }
    }
}

function damagePlayer(amount) {
    if (typeof playerHealth === 'undefined') {
        window.playerHealth = 100;
    }
    
    const healthBar = document.getElementById('player-health-bar');
    if (!healthBar) return;
    
    // Create damage effect
    showBattleEffect(amount, 'damage', '.player-health-bar');
    
    // Update health
    window.playerHealth = Math.max(0, window.playerHealth - amount);
    const healthPercent = (window.playerHealth / 100) * 100;
    healthBar.style.width = `${healthPercent}%`;
    healthBar.setAttribute('aria-valuenow', window.playerHealth);
    
    // Update battle message
    updateBattleMessage(false, amount);
    
    // Check if player is defeated
    if (window.playerHealth <= 0) {
        if (healthBar) healthBar.style.width = '0%';
        
        const battleMessage = document.getElementById('battle-message');
        if (battleMessage) {
            battleMessage.innerHTML = '<p class="text-danger mb-0">You have been defeated by the boss!</p>';
        }
        
        // End the battle after a short delay if player is defeated
        setTimeout(() => {
            window.showResults();
        }, 2000);
    }
}

// Battle effect function
function showBattleEffect(amount, type, targetSelector) {
    const target = document.querySelector(targetSelector);
    if (!target) return;
    
    const effect = document.createElement('div');
    effect.className = `battle-effect ${type}`;
    effect.textContent = type === 'damage' ? `-${amount}` : `+${amount}`;
    
    // Position randomly within the target
    const leftPos = 30 + Math.random() * 40;
    effect.style.left = `${leftPos}%`;
    
    target.appendChild(effect);
    
    // Remove the element after animation completes
    setTimeout(() => {
        effect.remove();
    }, 1500);
}

// Update battle message
function updateBattleMessage(playerAttacking, amount) {
    const messageElement = document.getElementById('battle-message');
    if (!messageElement) return;
    
    if (playerAttacking) {
        messageElement.innerHTML = `<p class="mb-0">You attacked the boss for <span class="text-danger">${amount}</span> damage!</p>`;
    } else {
        messageElement.innerHTML = `<p class="mb-0">The boss attacked you for <span class="text-danger">${amount}</span> damage!</p>`;
    }
}

// Initialize charts on the profile page
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