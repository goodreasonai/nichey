import { useEffect, useState } from "react";
import MarkdownViewer from "../../components/MarkdownViewer/MarkdownViewer";
import Head from "next/head";
import { useRouter } from "next/router";
import { useNavBar } from "@/components/NavBar/NavBar";
import DeleteIcon from '../../../public/DeleteIcon.png'
import EditIcon from '../../../public/EditIcon.png'
import Modal from "@/components/Modal/Modal";
import Button from "@/components/Button/Button";


export default function Article({}){

    const router = useRouter()
    const slug = router.query?.e

    const [entity, setEntity] = useState()
    const [entityFound, setEntityFound] = useState(undefined)
    const [isEditing, setIsEditing] = useState(false)
    const [showDelete, setShowDelete] = useState(false)
    const { setPath } = useNavBar()

    useEffect(() => {
        if (entity){
            setPath([
                {'href': {'pathname': `/articles`}, 'title': 'Articles'},
                {'href': {'pathname': `/article`, 'query': {'e': entity.slug}}, 'title': entity.title}
            ])
            return () => {
                setPath([])
            }
        }
        else {
            setPath([
                {'href': {'pathname': `/articles`}, 'title': 'Articles'}
            ])
            return () => {
                setPath([])
            }
        }
    }, [entity])

    async function getEntity(){
        try {
            const url = `${process.env.NEXT_PUBLIC_API}/api/page?slug=${slug}`
            const response = await fetch(url, {
                'method': 'GET'
            })
            if (!response.ok){
                throw Error("Response was not ok")
            }
            const myJson = await response.json()
            setEntity(myJson['entity'])
            setEntityFound(true)
        }
        catch(e) {
            console.log(e)
            setEntityFound(false)
        }
    }

    useEffect(() => {
        if (slug){
            getEntity()
        }
    }, [slug])

    async function saveChanges(){
        try {
            const url = `${process.env.NEXT_PUBLIC_API}/api/update-entity`
            const data = {
                'slug': slug,
                'markdown': entity?.markdown
            }
            const response = await fetch(url, {
                'headers': {
                    'Content-Type': 'application/json' 
                },
                'body': JSON.stringify(data),
                'method': 'POST'
            })
            if (!response.ok){
                throw Error("Could not save")
            }
            // Not doing anything with return yet
        }
        catch(e) {
            console.log(e)
        }
    }

    async function deletePage(){
        setShowDelete(false)
        try {
            const url = `${process.env.NEXT_PUBLIC_API}/api/delete-entity`
            const data = {
                'slug': slug,
            }
            const response = await fetch(url, {
                'headers': {
                    'Content-Type': 'application/json' 
                },
                'body': JSON.stringify(data),
                'method': 'POST'
            })
            if (!response.ok){
                throw Error("Could not save")
            }
            getEntity()
        }
        catch(e) {
            console.log(e)
        }
    }

    function onClickEdit(){
        if (isEditing){
            saveChanges()
        }
        setIsEditing(!isEditing)
    }

    const handleTextareaChange = (e) => {
        setEntity((prev) => {return {...prev, 'markdown': e.target.value}});
    }

    return (
        <div>
            <Head>
                <title>{entity?.title}</title>
            </Head>
            {entityFound === false ? (
                <div>
                    {`Could not find page for '${slug}'`}
                </div>
            ) : (entity?.markdown ? (
                isEditing ? (
                    <textarea onChange={handleTextareaChange} style={{'width': '100%', 'height': '75vh'}}>
                        {entity?.markdown}
                    </textarea>
                ) : (
                    <MarkdownViewer>
                        {entity?.markdown}
                    </MarkdownViewer>
                )
            ) : (
                <div>
                    {`Page for ${entity?.title} is not yet written.`}
                </div>
            ))}

            <div style={{'position': 'fixed', 'right': '10px', 'bottom': '10px', 'display': 'flex', 'gap': '10px', 'alignItems': 'center'}}>
                <div onClick={() => {setShowDelete(true)}} style={{'backgroundColor': 'var(--highlight)', 'border': '1px solid var(--border-color)', 'borderRadius': '5px', 'padding': '5px', 'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center'}}>
                    <img src={DeleteIcon.src} width={20} height={20} alt={"Delete"} />
                </div>
                <Modal title={"Delete"} isOpen={showDelete} close={() => setShowDelete(false)}>
                    <div style={{'display': 'flex', 'flexDirection': 'column', 'gap': '1rem', 'alignItems': 'center'}}>
                        <div>
                            {`Are you sure you would like to delete the page ${entity?.title}?`}
                        </div>
                        <div style={{'display': 'flex', 'gap': '10px'}}>
                            <Button value={"Delete"} onClick={() => deletePage()} />
                            <Button value={"Cancel"} onClick={() => {setShowDelete(false)}} />
                        </div>
                    </div>
                </Modal>
                <div onClick={onClickEdit} style={{'backgroundColor': 'var(--highlight)', 'border': '1px solid var(--border-color)', 'borderRadius': 'var(--small-border-radius)', 'padding': '5px', 'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center'}}>
                    {!isEditing ? (
                        <img src={EditIcon.src} width={20} height={20} alt={"Edit"} />
                    ) : (
                        "Save"
                    )}
                </div>
            </div>
        </div>
    )
}
