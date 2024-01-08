function sendMessage(message, type = "success") {
	setTimeout(function () {
		// setTimeout(function () {
		// 	window.location.reload();
		// }, 1000);

		const messages = document.getElementById("messages-list");
		messages.innerHTML = "";
		messages.innerHTML += `
<div class="alert alert-${type} alert-dismissible" role="alert" >
${message}
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
`;
	});
}
