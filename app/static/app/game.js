// We define the dice and rollButton elements here so that we can use them in multiple functions
const rollButton = document.getElementById("roll-button");
const dice = [...document.querySelectorAll(".die-list")];

// This function plays the dice animation.
// We use a Promise because the animation takes ~2 seconds to complete.
// So we need to wait for it to complete before proceeding.
function rollDice(roll, double) {
	return new Promise((resolve) => {
		// Set the button to hidden to prevent the user from clicking it again.
		rollButton.style.visibility = "hidden";
		const dice = [...document.querySelectorAll(".die-list")];

		// If the user has not rolled a double, we need to roll two dice.
		if (!double && roll.length >= 2) {
			toggleClasses(dice[0]);
			dice[0].dataset.roll = roll[0];
			toggleClasses(dice[2]);
			dice[2].dataset.roll = roll[1];
			// If the user has rolled a double, we only need to roll one die.
		} else if (double && roll.length >= 2) {
			toggleClasses(dice[1]);
			dice[1].dataset.roll = roll[2];
			// If this is a tiebraker, the roll array will only have one element.
			// So we need to roll one die.
		} else {
			toggleClasses(dice[1]);
			dice[1].dataset.roll = roll[0];
		}

		// Wait for the animation to finish before resolving the Promise.
		setTimeout(() => {
			resolve();
		}, 2000);
	});
}

// This toggles the classes for the dice for the animation.
function toggleClasses(die) {
	console.log(die.classList);
	die.classList.toggle("odd-roll");
	console.log(die.classList);
	die.classList.toggle("even-roll");
	console.log(die.classList);
}

// We define some key variables for the game information so we can update them.
const player = sessionStorage.getItem("username");

const opponent = document.getElementById("opponent");
const round = document.getElementById("round");
const yourScore = document.getElementById("yourScore");
const opponentScore = document.getElementById("opponentScore");
const playerRolling = document.getElementById("playerRolling");

// Set the button and dice to invisible to start.
rollButton.style.visibility = "hidden";
dice[0].style.visibility = "hidden";
dice[2].style.visibility = "hidden";
dice[1].style.visibility = "hidden";

// Set these game flags to false to start.
sessionStorage.setItem("rolling", false);
sessionStorage.setItem("tiebreaker", false);

// The handler for the roll button is defined.
// Since the websockets code is asynchronous, we need to keep track of the current handler.
// So we can remove it and add a new one, else they accumulate causing bugs.

let currentHandler = null;

// This code is run when the roll button is clicked.
const createRollButtonHandler = (res, socket) => {
	let doubleRolled = false;
	return async () => {
		// We play the animation with the first two dice.
		await rollDice(res.roll, doubleRolled);
		// If it is not a double, we set the rolling flag to false, hide the dice and send the acknowledgement.
		// We also do this if it is a double and the user has just rolled the third dice.
		if (!res.double || doubleRolled) {
			rollButton.style.visibility = "hidden";
			dice[0].style.visibility = "hidden";
			dice[2].style.visibility = "hidden";
			dice[1].style.visibility = "hidden";
			doubleRolled = false;
			sessionStorage.setItem("rolling", false);
			socket.send(JSON.stringify({}));
			// If it is a double, we set doubleRolled to true so we can exit the if statement.
			// We set the dice and button to visible and notify the user so they can click again.
		} else {
			doubleRolled = true;
			alert("You rolled a double! Click to roll again.");
			rollButton.style.visibility = "visible";
			dice[0].style.visibility = "hidden";
			dice[2].style.visibility = "hidden";
			dice[1].style.visibility = "visible";
		}
	};
};

// Define the websocket and connect to the server.
const socket = new WebSocket(sessionStorage.getItem("ws"));
socket.addEventListener("message", (event) => {
	const res = JSON.parse(event.data);

	// Here, we define the logic for each event.
	switch (res.message) {
		// If we receive a disconnect message, we alert the user and redirect them to the home page.
		case "player disconnected":
			alert(
				"Your opponent has disconnected so the game has been cancelled. You will be redirected to the home page."
			);
			window.location.href = "";
			break;

		// We ignore these messages.
		case "waiting for another player":
			break;

		case "not your turn":
			break;

		// When we receive the ready event, we update the game information.
		case "ready":
			if (player == res.player1) {
				opponent.innerHTML = "Opponent: " + res.player2;
			} else {
				opponent.innerHTML = "Opponent: " + res.player1;
			}
			round.innerHTML = "Round: 1";
			yourScore.innerHTML = "Your score: 0";
			opponentScore.innerHTML = "Opponent's score: 0";
			break;

		// When we receive the end event, we wait for any rolling animation to finish (hence the checkRolling function).
		// Then, we redirect them to the results page.
		case "end": {
			const checkRolling = async () => {
				if (sessionStorage.getItem("rolling") === "false") {
					window.location.href = window.location.href + "results/";
				} else {
					setTimeout(checkRolling, 100); // Check again after 100ms
				}
			};
			checkRolling();
			break;
		}

		// When we receive the update event, we update the game information.
		case "update":
			if (res.player == player) {
				yourScore.innerHTML = "Your score: " + res.score;
			} else {
				opponentScore.innerHTML = "Opponent's score: " + res.score;
			}
			round.innerHTML = "Round: " + res.round;
			playerRolling.innerHTML = "Opponent's turn...";
			break;

		// When we receive the roll event, we let the user roll the dice with pre-determined values from the server.
		// We do this by resetting the button handler and making the dice visible.
		// If there is already a rolling animation going on, we wait for that first.
		case "your roll": {
			const checkRolling = async () => {
				if (sessionStorage.getItem("rolling") === "false") {
					playerRolling.innerHTML = "Your turn!";
					rollButton.style.visibility = "visible";
					if (!res.tiebreaker) {
						dice[0].style.visibility = "visible";
						dice[2].style.visibility = "visible";
						dice[1].style.visibility = "hidden";
					} else {
						// If this is a tiebraker, the roll array will only have one element.
						if (sessionStorage.getItem("tiebreaker") === "false") {
							alert(
								"You tied! Continue rolling until one player gets a higher roll."
							);
							sessionStorage.setItem("tiebreaker", true);
						}
						dice[0].style.visibility = "hidden";
						dice[2].style.visibility = "hidden";
						dice[1].style.visibility = "visible";
					}
					// We set rolling to true to prevent other code running.
					sessionStorage.setItem("rolling", true);
					if (currentHandler) {
						rollButton.removeEventListener("click", currentHandler);
					}
					currentHandler = createRollButtonHandler(res, socket);
					rollButton.addEventListener("click", currentHandler);
				} else {
					setTimeout(checkRolling, 100); // Check again after 100ms
				}
			};
			checkRolling();
			break;
		}

		// This default case runs when we receive the pre_update event which contains the other player's roll so we can animate it.
		default: {
			const checkRolling = async () => {
				if (sessionStorage.getItem("rolling") === "false") {
					playerRolling.innerHTML = "Opponent's turn...";
					rollButton.style.visibility = "hidden";
					if (!res.tiebreaker) {
						dice[0].style.visibility = "visible";
						dice[2].style.visibility = "visible";
						dice[1].style.visibility = "hidden";
					} else {
						if (sessionStorage.getItem("tiebreaker") === "false") {
							alert(
								"You tied! Continue rolling until one player gets a higher roll."
							);
							sessionStorage.setItem("tiebreaker", true);
						}
						dice[0].style.visibility = "hidden";
						dice[2].style.visibility = "hidden";
						dice[1].style.visibility = "visible";
					}
					sessionStorage.setItem("rolling", true);
					// We roll the dice with the pre-determined values from the server.
					await rollDice(res.roll, false);
					if (!res.double) {
						sessionStorage.setItem("rolling", false);
					} else {
						// If it's a double, we do it again.
						alert("They rolled a double!");
						dice[0].style.visibility = "hidden";
						dice[2].style.visibility = "hidden";
						dice[1].style.visibility = "visible";
						await rollDice(res.roll, true);
						dice[1].style.visibility = "hidden";
						sessionStorage.setItem("rolling", false);
					}
				} else {
					setTimeout(checkRolling, 100);
				}
			};
			checkRolling();
			break;
		}
	}
});
