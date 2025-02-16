import { getRandomId } from "@/utils/random";
import Link from "next/link";
import { useCallback, useState, createContext, useContext, useRef, useEffect } from 'react'


export default function NavBar({}) {

    const { path } = useNavBar()

    return (
        <div style={{'display': 'flex', 'gap': '10px', 'alignItems': 'center'}}>
            <Link href={"/"}>Home</Link>
            {path.map((x) => {
                return (
                    <>
                        <div style={{'fontSize': '12pt'}}>{'>'}</div>
                        <Link href={x.href}>
                            {`${x.title}`}
                        </Link>
                    </>
                )
            })}
        </div>
    )
}

const NavBarContext = createContext();

export const useNavBar = () => {
    return useContext(NavBarContext);
};

export const NavBarProvider = ({ children }) => {
    const [path, setPath] = useState([]);

    return (
        <NavBarContext.Provider value={{ path, setPath }}>
            {children}
        </NavBarContext.Provider>
    );
};
