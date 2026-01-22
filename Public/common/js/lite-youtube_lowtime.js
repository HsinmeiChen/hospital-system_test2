 function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
  }

  function init_Youtube(id){

   console.log(id)
   let playerElement=document.querySelector(`#${id} div.youtube-player`)

   let videoId = playerElement.dataset.id;
   localStorage.setItem("videoId",videoId)
   let iframe = document.createElement('iframe');
    iframe.setAttribute('src', 'https://www.youtube.com/embed/' + videoId + '?rel=0');
    iframe.setAttribute('frameborder', '1');
    iframe.setAttribute('allowfullscreen', '1');
    // iframe.setAttribute('autoplay','1');
    // 
    iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share','autoload');
    iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
    iframe.setAttribute('loading', 'lazy');
    playerElement.parentNode.replaceChild(iframe, playerElement);
  }

  function close_Youtube(id){
   console.log(id)
   let playerElement=document.querySelector(`#${id} div.embed-container`)
   let videoId=localStorage.getItem('videoId')

   removeAllChildNodes(playerElement)
   let div=document.createElement("div")
   div.setAttribute("data-id",videoId)
   div.setAttribute("class","youtube-player")

    
    playerElement.appendChild(div);
  }


  //document.addEventListener('DOMContentLoaded', initYouTubeVideos);
  $('.modal').on('hide.bs.modal',function(){
   // $('iframe').detach();
   id=$(this).attr('id')
   if(/^D[0-9]+-[0-9]+$/.test(id))
    close_Youtube(id)
   // close_Youtube(id)
   //initYouTubeVideos()
  })

  
  $('.modal').on('show.bs.modal',function(){
   // $('iframe').detach();
   id=$(this).attr('id')
   if(/^D[0-9]+-[0-9]+$/.test(id))
    init_Youtube(id)

   //initYouTubeVideos()
  })

