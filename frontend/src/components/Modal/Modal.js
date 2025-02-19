import CloseIcon from '../../../public/CloseIcon.png'
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom'
import styles from './Modal.module.css'


export default function Modal({ isOpen, close, title, minWidth="500px", minHeight="unset", style, children}) {

    const modalOverlayRef = useRef(null)
    const modalContainerRef = useRef(null)
    const containerContainerRef = useRef(null)

    useEffect(() => {
    
        const handleClickOutside = (event) => {
            if (event.target === modalOverlayRef.current) {
                close();
            }
        };
    
        try {
            if (isOpen) {
                window.addEventListener('mousedown', handleClickOutside, { capture: true });
            }
            else {
                window.removeEventListener('mousedown', handleClickOutside, { capture: true });
            }
        } catch(e) {}
    
        return () => {
            try {
                window.removeEventListener('mousedown', handleClickOutside, { capture: true });
            } catch(e){}
        };
    }, [isOpen, close]);


    if (!isOpen){
        return ""
    }
    return (
        ReactDOM.createPortal(
            <div className={styles.overlay} style={style} ref={modalOverlayRef}>
                <div className={styles.containerContainer} ref={containerContainerRef} style={{'overflow': 'hidden', 'transition': 'all .1s linear'}}>
                    <div className={styles.container} style={{}} ref={modalContainerRef}>
                        <div className={styles.header}>
                            <div className={styles.title}>
                                {title}
                            </div>
                            <div style={{'display': 'flex', 'alignItems': 'center'}} onClick={() => {close()}}>
                                <img src={CloseIcon.src} style={{'cursor': 'pointer'}} onClick={close} alt={"Close"} width={17} height={17} />
                            </div>
                        </div>
                        <div className={styles.body}>
                            {children}
                        </div>
                    </div>
                </div>
            </div>,
            document.body
        )
    )
}
