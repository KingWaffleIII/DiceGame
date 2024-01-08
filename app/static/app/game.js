const rollButton = document.getElementById("roll-button");
const dice = [...document.querySelectorAll(".die-list")];

function rollDice(roll, double) {
	return new Promise((resolve) => {
		rollButton.style.visibility = "hidden";
		const dice = [...document.querySelectorAll(".die-list")];

		if (!double && roll.length >= 2) {
			toggleClasses(dice[0]);
			dice[0].dataset.roll = roll[0];
			toggleClasses(dice[2]);
			dice[2].dataset.roll = roll[1];
		} else if (double && roll.length >= 2) {
			toggleClasses(dice[1]);
			dice[1].dataset.roll = roll[2];
		} else {
			toggleClasses(dice[1]);
			dice[1].dataset.roll = roll[0];
		}

		setTimeout(() => {
			resolve();
		}, 2000);
	});
}

function toggleClasses(die) {
	console.log(die.classList);
	die.classList.toggle("odd-roll");
	console.log(die.classList);
	die.classList.toggle("even-roll");
	console.log(die.classList);
}

const player = sessionStorage.getItem("username");

const opponent = document.getElementById("opponent");
const round = document.getElementById("round");
const yourScore = document.getElementById("yourScore");
const opponentScore = document.getElementById("opponentScore");
const playerRolling = document.getElementById("playerRolling");

// set roll button and dice to hidden
rollButton.style.visibility = "hidden";
dice[0].style.visibility = "hidden";
dice[2].style.visibility = "hidden";
dice[1].style.visibility = "hidden";

sessionStorage.setItem("rolling", false);
sessionStorage.setItem("tiebreaker", false);

let currentHandler = null;

const createRollButtonHandler = (res, socket) => {
	let doubleRolled = false;
	return async () => {
		await rollDice(res.roll, doubleRolled);
		if (!res.double || doubleRolled) {
			rollButton.style.visibility = "hidden";
			dice[0].style.visibility = "hidden";
			dice[2].style.visibility = "hidden";
			dice[1].style.visibility = "hidden";
			doubleRolled = false;
			sessionStorage.setItem("rolling", false);
			socket.send(JSON.stringify({}));
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

const socket = new WebSocket(sessionStorage.getItem("ws"));
socket.addEventListener("message", (event) => {
	const res = JSON.parse(event.data);

	switch (res.message) {
		// error handling
		case "player disconnected":
			alert(
				"Your opponent has disconnected so the game has been cancelled. You will be redirected to the home page."
			);
			window.location.href = "";
			break;

		case "waiting for another player":
			break;

		case "not your turn":
			break;

		// game logic
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

		case "update":
			if (res.player == player) {
				yourScore.innerHTML = "Your score: " + res.score;
			} else {
				opponentScore.innerHTML = "Opponent's score: " + res.score;
			}
			round.innerHTML = "Round: " + res.round;
			playerRolling.innerHTML = "Opponent's turn...";
			break;

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
					await rollDice(res.roll, false);
					if (!res.double) {
						sessionStorage.setItem("rolling", false);
					} else {
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
