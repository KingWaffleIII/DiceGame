$("body").on("click", ".dice", () => {
	const roll = Math.floor(Math.random() * 6 + 1);
	$(this).attr("class", "dice");
	setTimeout(function () {
		$(".dice").addClass("roll-" + roll);
	}, 1);
	setTimeout(function () {
		// update p1-Score and add the old score
		const p1Score = document.getElementById("p1-score");
		const oldP1Score = parseInt(p1Score.innerHTML);
		p1Score.innerHTML = oldP1Score + roll;
	}, 2500);
});
