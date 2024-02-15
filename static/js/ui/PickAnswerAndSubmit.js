function PickAnswerAndSubmit(root) {
  document.querySelector('#unsure-and-submit').addEventListener('click', function (e) {
    e.preventDefault()
    var answer = document.querySelector('input[value="' + root.dataset.answerToPick + '"]')
    answer.checked = true
    document.querySelector('#contribution-form').submit()
  })
}

export default PickAnswerAndSubmit
