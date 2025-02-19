import { useEffect, useState } from "react";
import MarkdownViewer from "../../components/MarkdownViewer/MarkdownViewer";
import Head from "next/head";
import { useRouter } from "next/router";
import { useNavBar } from "@/components/NavBar/NavBar";
import DeleteIcon from '../../../public/DeleteIcon.png'
import Modal from "@/components/Modal/Modal";
import Button from "@/components/Button/Button";


export default function Source({}){

    const router = useRouter()
    const id = router.query?.id

    const [source, setSource] = useState()
    const [sourceFound, setSourceFound] = useState(undefined)
    const [showDelete, setShowDelete] = useState(false)
    const { setPath } = useNavBar()

    useEffect(() => {
        if (source){
            setPath([
                {'href': {'pathname': `/sources`}, 'title': 'Sources'},
                {'href': {'pathname': `/source`, 'query': {'id': source.id}}, 'title': source.title}
            ])
            return () => {
                setPath([])
            }
        }
        else {
            setPath([
                {'href': {'pathname': `/sources`}, 'title': 'Sources'}
            ])
            return () => {
                setPath([])
            }
        }
    }, [source])

    async function getSource(){
        try {
            const url = `${process.env.NEXT_PUBLIC_API}/api/source?id=${id}`
            const response = await fetch(url, {
                'method': 'GET'
            })
            if (!response.ok){
                throw Error("Response was not ok")
            }
            const myJson = await response.json()
            setSource(myJson['source'])
            setSourceFound(true)
        }
        catch(e) {
            console.log(e)
            setSourceFound(false)
        }
    }

    useEffect(() => {
        if (id){
            getSource()
        }
    }, [id])

    async function deletePage(){
        setShowDelete(false)
        try {
            const url = `${process.env.NEXT_PUBLIC_API}/api/delete-source`
            const data = {
                'id': id,
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
            getSource()
        }
        catch(e) {
            console.log(e)
        }
    }

    const info = [
        {'label': 'URL', 'value': (
            <a href={source?.url}>{source?.url}</a>
        ), 'hidden': !source?.url},
        {'label': 'Search Engine', 'value': source?.search_engine, 'hidden': !source?.search_engine},
        {'label': 'Query', 'value': source?.query, 'hidden': !source?.query},
        {'label': 'Snippet', 'value': source?.snippet, 'hidden': !source?.snippet}
    ]

    return (
        <div>
            <Head>
                <title>{source?.title}</title>
            </Head>
            {sourceFound === false ? (
                <div>
                    {`Could not find source with id '${id}'`}
                </div>
            ) : (source ? (
                <div style={{'display': 'flex', 'flexDirection': 'column', 'gap': '1rem'}}>
                    <h1>
                        {source.title}
                    </h1>
                    {info.filter((x) => !x.hidden).map((item) => {
                        return (
                            <div style={{'display': 'flex'}}>
                                <div style={{'flex': '1'}}>
                                    {item.label}
                                </div>
                                <div style={{'flex': '1'}}>
                                    {item.value}
                                </div>
                            </div>
                        )
                    })}
                </div>
            ) : "")}

            <div style={{'position': 'fixed', 'right': '10px', 'bottom': '10px', 'display': 'flex', 'gap': '10px', 'alignItems': 'center'}}>
                <div onClick={() => {setShowDelete(true)}} style={{'backgroundColor': 'var(--highlight)', 'border': '1px solid var(--border-color)', 'borderRadius': '5px', 'padding': '5px', 'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center'}}>
                    <img src={DeleteIcon.src} width={20} height={20} alt={"Delete"} />
                </div>
                <Modal title={"Delete"} isOpen={showDelete} close={() => setShowDelete(false)}>
                    <div style={{'display': 'flex', 'flexDirection': 'column', 'gap': '1rem', 'alignItems': 'center'}}>
                        <div>
                            {`Are you sure you would like to delete the source ${source?.title}?`}
                        </div>
                        <div style={{'display': 'flex', 'gap': '10px'}}>
                            <Button value={"Delete"} onClick={() => deletePage()} />
                            <Button value={"Cancel"} onClick={() => {setShowDelete(false)}} />
                        </div>
                    </div>
                </Modal>
            </div>
        </div>
    )
}
