<template lang="pug">
	.c-media-source(:class="{'in-background': background, 'in-room-manager': inRoomManager}")
		transition(name="background-room")
			router-link.background-room(v-if="background", :to="room ? {name: 'room', params: {roomId: room.id}}: {name: 'channel', params: {channelId: call.channel}}")
				.description
					.hint {{ $t('MediaSource:room:hint') }}
					.room-name(v-if="room") {{ room.name }}
					.room-name(v-else="call") {{ $t('MediaSource:call:label') }}
				.global-placeholder
				bunt-icon-button(@click.prevent.stop="$emit('close')") close
		livestream(v-if="room && module.type === 'livestream.native'", ref="livestream", :room="room", :module="module", :size="background ? 'tiny' : 'normal'", :key="`livestream-${room.id}`")
		janus-call(v-else-if="room && module.type === 'call.janus'", ref="janus", :room="room", :module="module", :background="background", :size="background ? 'tiny' : 'normal'", :key="`janus-${room.id}`")
		janus-channel-call(v-else-if="call", ref="janus", :call="call", :background="background", :size="background ? 'tiny' : 'normal'", :key="`call-${call.id}`", @close="$emit('close')")
		.iframe-error(v-if="iframeError") {{ $t('MediaSource:iframe-error:text') }}
		//- iframe#video-player-translation(v-if="languageIframeUrl", :src="languageIframeUrl", style="position: absolute; width: 50%; height: 100%; z-index: -1", frameborder="0", gesture="media", allow="autoplay; encrypted-media", allowfullscreen="true")
	</template>
	<script>
	// TODO functional component?
	import { mapState, mapGetters } from 'vuex'
	import isEqual from 'lodash/isEqual'
	import api from 'lib/api'
	import JanusCall from 'components/JanusCall'
	import JanusChannelCall from 'components/JanusChannelCall'
	import Livestream from 'components/Livestream'
	
	export default {
		components: { Livestream, JanusCall, JanusChannelCall },
		props: {
			room: Object,
			call: Object,
			background: {
				type: Boolean,
				default: false
			}
		},
		data () {
			return {
				iframeError: null,
				iframe: null, // Track the iframe element
				languageAudioUrl: null, // URL for the selected language audio
				languageIframeUrl: null, // URL for the language iframe // Added languageIframeUrl to data
				videoPlayer: null,
				  audioPlayer: null,
			}
		},
		computed: {
			...mapState(['streamingRoom', 'youtubeTransUrl', 'activeRoom']),
			...mapGetters(['autoplay']),
			module () {
				if (!this.room) {
					return null
				}
				return this.room.modules.find(module => ['livestream.native', 'livestream.youtube', 'livestream.iframe', 'call.bigbluebutton', 'call.janus', 'call.zoom'].includes(module.type))
			},
			inRoomManager () {
				return this.$route.name === 'room:manage'
			}
		},
		watch: {
			background () {
				if (!this.iframe) return
				if (this.background) {
					this.iframe.classList.add('background')
				} else {
					this.iframe.classList.remove('background')
				}
			},
			module: {
				handler (value, oldValue) {
					if (isEqual(value, oldValue)) return
					this.destroyIframe()
					this.initializeIframe(false)
				}
			},
			youtubeTransUrl(youtubeTransUrl) {
				if (!this.room) {
					return
				}
				this.destroyIframe()
				this.module.config.ytid = youtubeTransUrl
				this.initializeIframe(false)
			},
			// activeRoom() {
			// 	this.handleRoomChange()
			// }
		},
		async mounted () {
			if (!this.room) {
				return
			}
			this.initializeIframe(false)
			this.$root.$on('languageChanged', this.handleLanguageChange);
			// this.$root.$on('changeRoom', this.handleRoomChange);
		},
		beforeDestroy () {
			console.log('dessssssss')
			this.iframe?.remove()
			// const videoIframe = document.getElementById('video-player')
			// videoIframe?.remove()
			// const audioIframe = document.getElementById('audio-player')
			// audioIframe?.remove()
			// this.videoPlayer = null
			// this.audioPlayer = null
			if (api.socketState !== 'open') return
			// TODO move to store?
			if (this.room) api.call('room.leave', {room: this.room.id})
			this.$root.$off('languageChanged', this.handleLanguageChange);
		},
		methods: {

			// handleRoomChange () {
			// 	console.log("sssssssssssss", this.module.config.ytid)
			// 	const videoIframe = document.getElementById('video-player')
			// 	videoIframe?.remove()
			// 	const audioIframe = document.getElementById('audio-player')
			// 	audioIframe?.remove()
			// 	this.videoPlayer = null
			// 	this.audioPlayer = null
			// 	this.initializeVideo()
			// },

			async initializeIframe (mute) {
				try {
					let iframeUrl
					let hideIfBackground = false
					switch (this.module.type) {
						case 'call.bigbluebutton': {
							({url: iframeUrl} = await api.call('bbb.room_url', {room: this.room.id}))
							hideIfBackground = true
							break
						}
						case 'call.zoom': {
							({url: iframeUrl} = await api.call('zoom.room_url', {room: this.room.id}))
							hideIfBackground = true
							break
						}
						case 'livestream.iframe': {
							iframeUrl = this.module.config.url
							break
						}
						case 'livestream.youtube': {
							iframeUrl = this.getYoutubeUrl(this.module.config.ytid, this.autoplay, mute)
							if (!window.YT) {
								const tag = document.createElement('script');
								tag.src = 'https://www.youtube.com/iframe_api';
								const firstScriptTag = document.getElementsByTagName('script')[0];
								firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
					
								window.onYouTubeIframeAPIReady = this.initializeVideo;
							} else {
								this.initializeVideo();
							}
							return
						}
					}
					if (!iframeUrl || !this.$el || this._isDestroyed) return
					const iframe = document.createElement('iframe')
					iframe.src = iframeUrl
					iframe.classList.add('iframe-media-source')
					if (hideIfBackground) {
						iframe.classList.add('hide-if-background')
					}
					iframe.allow = 'screen-wake-lock *; camera *; microphone *; fullscreen *; display-capture *' + (this.autoplay ? '; autoplay *' : '')
					iframe.allowfullscreen = true
					iframe.allowusermedia = true
					iframe.setAttribute('allowfullscreen', '') // iframe.allowfullscreen is not enough in firefox#media-source-iframes
					const container = document.querySelector('#media-source-iframes')
					container.appendChild(iframe)
					this.iframe = iframe
				} catch (error) {
					// TODO handle bbb/zoom.join.missing_profile
					this.iframeError = error
					console.error(error)
				}
			},
			destroyIframe () {
				this.iframe?.remove()
				this.iframe = null
			},
			isPlaying () {
				if (this.call) {
					return this.$refs.janus.roomId
				}
				if (this.module.type === 'livestream.native') {
					return this.$refs.livestream.playing && !this.$refs.livestream.offline
				}
				if (this.module.type === 'call.janus') {
					return this.$refs.janus.roomId
				}
				if (this.module.type === 'call.bigbluebutton') {
					return !!this.iframe
				}
				if (this.module.type === 'call.zoom') {
					return !!this.iframe
				}
				return true
			},
			handleLanguageChange(languageUrl) {
				this.languageAudioUrl = languageUrl; // Set the audio source to the selected language URL
				// const mute = !!languageUrl; // Mute if language URL is present, otherwise unmute
				// this.destroyIframe();
				// this.initializeIframe(mute); // Initialize iframe with the appropriate mute state
				// Set the language iframe URL when language changes
				this.languageIframeUrl = this.getLanguageIframeUrl(languageUrl);
				
				if (this.audioPlayer == null) {
					this.initializeAudio(languageUrl)
				}
				else {
					this.audioPlayer.loadVideoById(languageUrl, 5, "large")
				}	
			},
			getYoutubeUrl(ytid, autoplay, mute) {
				// Construct the autoplay parameter based on the input
				const autoplayParam = autoplay ? 'autoplay=1&' : '';
				// Construct the mute parameter based on the input
				const muteParam = mute ? 'mute=1' : 'mute=0';
				// Return the complete YouTube URL with the provided video ID, autoplay, and mute parameters
				return `https://www.youtube-nocookie.com/embed/${ytid}?${autoplayParam}rel=0&showinfo=0&${muteParam}`;
			},
			// Added method to get the language iframe URL
			getLanguageIframeUrl(languageUrl) {
				// Checks if the languageUrl is not provided the retun null
				if (!languageUrl) return null;
				return `https://www.youtube.com/embed/${languageUrl}?enablejsapi=1&autoplay=1&modestbranding=1&loop=1&controls=0&disablekb=1&languageUrl=${languageUrl}`;
			},
			initializeVideo() {
				// let videoIframe = document.getElementById('video-player')
				// if(!videoIframe || videoIframe.tagName.toLowerCase() === 'iframe') {
				// 	videoIframe?.remove()
				// 	videoIframe = document.createElement('div')
				// 	videoIframe.id = 'video-player'
				// 	videoIframe.classList.add('iframe-media-source')
				// 	const container = document.querySelector('#media-source-iframes')
				// 	container.appendChild(videoIframe)
				// }
				
				if (this.videoPlayer != null) {
					this.audioPlayer.loadVideoById(this.module.config.ytid, 5, "large")
					return
				}

				this.videoPlayer = new YT.Player('video-player', {
					videoId: this.module.config.ytid, // Replace with the ID of the video you want to display
					events: {
						'onReady': this.onVideoPlayerReady,
						'onStateChange': this.onPlayerStateChange,
					},
					playerVars: {
						'autoplay': 1
					},
				});
			},
			initializeAudio(id) {
				// let audioIframe = document.getElementById('audio-player')
				// if(!audioIframe) {
				// 	audioIframe = document.createElement('div')
				// 	audioIframe.id = 'video-player'
				// 	audioIframe.style = "display: none"
				// 	const container = document.querySelector('#media-source-iframes')
				// 	container.appendChild(audioIframe)
				// }

				this.audioPlayer = new YT.Player('audio-player', {
					videoId: id, // Replace with the ID of the video whose audio you want to use
					events: {
						'onReady': this.onAudioPlayerReady,
					},
				});
			},
	
	
			onAudioPlayerReady(event) {
				// event.target.mute();
				this.videoPlayer.pauseVideo()
				this.videoPlayer.mute()
				event.target.seekTo(this.videoPlayer.getCurrentTime())
				const video_player = this.videoPlayer;
				setTimeout(() => {
					video_player.playVideo()
				}, 10)
	
			},
			onPlayerStateChange(event) {
				if(this.audioPlayer) {
					if (event.data === YT.PlayerState.PLAYING) {
						this.audioPlayer.seekTo(this.videoPlayer.getCurrentTime());
						this.audioPlayer.unMute();
						this.audioPlayer.playVideo();
					} else if (event.data === YT.PlayerState.PAUSED) {
						this.audioPlayer.pauseVideo();
					} else if (event.data === YT.PlayerState.ENDED) {
						this.audioPlayer.stopVideo();
					}
				}
				
			},
			onVideoPlayerReady(event) {
				// Mute the video player
				// console.log('event.target',event.target.getPlayerState())
				// event.target.mute();
				// event.target.playVideo();
			},
		}
	}
	</script>
	<style lang="stylus">
	.c-media-source
		position: absolute
		width: 0
		height: 0
		&.in-background
			z-index: 101
		.background-room
			position: fixed
			top: 3px
			right: 4px
			card()
			display: flex
			align-items: center
			height: 48px
			min-width: 280px
			max-width: 380px
			.description
				flex: auto
				align-self: stretch
				padding: 4px 8px
				max-width: 238px
				.hint
					color: $clr-secondary-text-light
					font-size: 10px
					margin-bottom: 2px
				.room-name
					color: var(--clr-text-primary)
					font-weight: 500
					flex-grow: 0
					ellipsis()
			.global-placeholder
				width: 86px
				flex: none
			.bunt-icon-button
				icon-button-style(style: clear)
				margin: 0 2px
			+below('l')
				top: 51px
		.background-room-enter-active, .background-room-leave-active
			transition: transform .3s ease
		// .background-room-enter-active
		// 	transition-delay: .1s
		.background-room-enter, .background-room-leave-to
			transform: translate(calc(-1 * var(--chatbar-width)), 52px)
	.c-media-source .c-livestream, .c-media-source .c-januscall, .c-media-source .c-januschannelcall, iframe.iframe-media-source
		position: fixed
		transition: all .3s ease
		&.size-tiny, &.background
			bottom: calc(var(--vh100) - 48px - 3px)
			right: 4px + 36px + 4px
			+below('l')
				bottom: calc(var(--vh100) - 48px - 48px - 3px)
		&:not(.size-tiny):not(.background)
			bottom: calc(var(--vh100) - 56px - var(--mediasource-placeholder-height))
			right: calc(100vw - var(--sidebar-width) - var(--mediasource-placeholder-width))
			width: var(--mediasource-placeholder-width)
			height: var(--mediasource-placeholder-height)
			+below('l')
				bottom: calc(var(--vh100) - 48px - 56px - var(--mediasource-placeholder-height))
				right: calc(100vw - var(--mediasource-placeholder-width))
	iframe.iframe-media-source
		transition: all .3s ease
		border: none
		&.background
			pointer-events: none
			height: 48px
			width: 86px
			z-index: 101
			&.hide-if-background
				width: 0
				height: 0
	</style>
	