const $liked_unliked  = $('.liked_unliked')
const $send_new_message = $('#send_new_message')

const $ProcessMessages = new ProcessMessages()


$liked_unliked.submit(async (e) =>{
    e.preventDefault();

    const $form = e.target
    
    const $result = await $ProcessMessages.likeUnlikedMessage($form)
    const $btn = $($form).find("button")

    if($result['data'].resp){
        $btn.toggleClass("btn-secondary")
        $btn.toggleClass("btn-primary")
    }else{
        $btn.toggleClass("btn-secondary")
        $btn.toggleClass("btn-primary")
    }

})


$send_new_message.submit(async (e) =>{
    e.preventDefault();

    const $form = e.target
    const $result = await $ProcessMessages.sendNewMessage($form)

    if($result['data'].resp){
        $('#message_body').val("message has been sent")
    }else{
        $('#message_body').val("message has not been sent")
    }
   

})


