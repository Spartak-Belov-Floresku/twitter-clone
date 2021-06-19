BASE_URL = '/'


class ProcessMessages{

    async likeUnlikedMessage(form){

        const $json = this.getData(form)

        return await axios.patch(`${BASE_URL}api/add_like/message`,{
                                    $json
                                }).then( responce => {
                                    return responce
                                }).catch(err => {
                                    console.log(err)
                                });
    }

    async sendNewMessage(form){

        const $json = this.getData(form)

        return await axios.post(`${BASE_URL}api/messages/new`,{
                                    $json
                                }).then( responce => {
                                    return responce
                                }).catch(err => {
                                    console.log(err)
                                });

    }

    getData(form){
        return $(form).serializeArray().reduce((obj, item) => {
            obj[item.name] = item.value;
            return obj;
        }, {})
    }
    

}
