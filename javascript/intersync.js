function log(str) {
    console.log('[intersync] ' + str);
}

var lastTaskId = null;

function init() {
    const send = initSocket();

    const observer = new MutationObserver((mutationList, observer) => {
        for (const mutation of mutationList) {
            if (mutation.addedNodes.length == 1 && mutation.addedNodes[0].className == 'progressDiv') {
                const taskId = localStorage.getItem("txt2img_task_id");
                if (lastTaskId == taskId)
                    continue;
                send(JSON.stringify({
                    'type': 'progress',
                    'data': taskId
                }));
            }
        }
    });
    observer.observe(gradioApp().getElementById('txt2img_results'), { childList: true });
}

function putResult(id) {
    fetch('/intersync/result/' + id)
        .then(response => response.json())
        .then(json => {
/*            {
                images: [imgToB64(img) for img in data[0]],
                generation_info: data[1],
                html_info: data[2],
                html_log: data[3]
            }*/
            const img = document.createElement('img');
            img.src = json.images[0];
            gradioApp().appendChild(img);
        })
        .catch(err => console.error(err));
}

function initSocket() {
    var socket = new WebSocket('ws://' + window.location.host + '/intersync/connect');
    socket.onopen = e => {
        log('Connected');
    };

    socket.onmessage = e => {
        const msg = JSON.parse(e.data);
        switch (msg.type) {
        case 'progress':
            const id = msg.data;
            lastTaskId = id;
            rememberGallerySelection('txt2img_gallery');
            showSubmitButtons('txt2img', false);
            localStorage.setItem("txt2img_task_id", id);
            requestProgress(id, gradioApp().getElementById('txt2img_gallery_container'), gradioApp().getElementById('txt2img_gallery'), function(){
                showSubmitButtons('txt2img', true);
                localStorage.removeItem("txt2img_task_id");
                showRestoreProgressButton('txt2img', false);
                putResult(id);
            });
            break;
        }
    };

    socket.onclose = e => {
        log('Disconnected');
        // reconnect
        //socket = null;
        //setTimeout(() => initSocket(socket), 5000);
    };

    socket.onerror = e => {
        log('Error');
        console.error(e);
    };

    return data => {
        socket.send(data);
    };
}

onUiLoaded(init);
